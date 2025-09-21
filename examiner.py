import cv2
import time
import math
from ultralytics import YOLO
import logging
from config import CAMERA, VIRTUAL, USER, INTERVAL, RELATIVE_DISTANCE, FPS_DEFAULT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 设置模型
model = YOLO('yolo11n-pose.pt')

def distance(a, b):
    """计算两点之间的欧几里得距离"""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def validate_results(results):
    """验证YOLO的输出是否有效"""
    if len(results) == 0:
        return False
    
    if not hasattr(results[0], "keypoints") or results[0].keypoints is None:
        return False
    
    xy = results[0].keypoints.xy
    if xy is None or xy.shape[0] == 0:
        return False
    
    kpts = xy[0].cpu().numpy()
    if kpts.shape[0] < 17:
        return False
    
    return True

def detect_fall(head, foot, hf_distance, last_fall_moment):
    """检测摔倒"""
    current_time = time.time()
    if current_time - last_fall_moment <= INTERVAL:
        return False, ""
    
    # 头部运动距离
    if head[0] is not None and head[-1] is not None:
        move_distance = distance(head[0], head[-1])
    else:
        move_distance = 0

    is_falling = (
        (move_distance >= RELATIVE_DISTANCE * hf_distance and hf_distance != 0)
    )
    
    if is_falling:
        logging.warning("DETECTED FALLING!!!!!")
        
        record = time.strftime("%Y%m%d-%H-%M-%S", time.localtime(current_time))
        return True, record
    
    return False, ""

def record_fall_frames(record_time, user, frames, fps):
    """记录摔倒相关帧"""
    return [
        record_time,
        user,
        frames[0],              # 摔倒前1秒
        frames[fps//2],         # 摔倒前0.5秒
        frames[-1]              # 摔倒时刻
    ]

def examiner(fqueue, rqueue):
    """视频帧处理函数"""
    cap = cv2.VideoCapture(CAMERA)  # 打开摄像头
    fps = int(cap.get(cv2.CAP_PROP_FPS))  # 获取摄像头的帧率
    if VIRTUAL == 1:
        fps = FPS_DEFAULT

    logging.info(f"FPS now is: {fps}")

    is_recording = False  # 是否正在记录摔倒

    # 摔倒的格式化时间，用于添加记录
    record = ""
    fall_record = []
    
    head = []
    foot = []
    frames = []
    
    hf_distance = 0
    last_fall_moment = 0

    # 遍历视频帧
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            logging.info("end")
            break

        frames.append(frame)
        if len(frames) > int(fps):
            del frames[0]

        results = model.track(frame)
        
        # 先显示图像
        if len(results) > 0:
            annotated_frame = results[0].plot()
        else:
            annotated_frame = frame
        cv2.imshow("YOLO推理", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        # 记录头部和脚部位置，无检测时标记为 None
        if not validate_results(results):
            head.append(None)
            foot.append(None)
        else:
            xy = results[0].keypoints.xy
            kpts = xy[0].cpu().numpy()
            
            head_position = [int(kpts[0][0]), int(kpts[0][1])]
            if head_position[0] == 0 and head_position[1] == 0:
                head.append(None)
            else:
                head.append(head_position)
            
            foot_position1 = [int(kpts[15][0]), int(kpts[15][1])]
            foot_position2 = [int(kpts[16][0]), int(kpts[16][1])]
            
            if ((foot_position1[0] == 0 and foot_position1[1] == 0) or 
                (foot_position2[0] == 0 and foot_position2[1] == 0)):
                foot.append(None)
            else:
                # 如果两个脚部位置都有效，选择距离头部最远的
                foot.append(max(foot_position1, foot_position2, 
                              key=lambda x: distance(x, head_position)))
         
        
        if len(head) > fps:
            del head[0]
            del foot[0]

        if is_recording == True and time.time()-last_fall_moment >= 0.5:
            is_recording = False
            fall_record.append(frame)
            rqueue.put(fall_record)
            logging.info("Finish Record")
            logging.info(f"Queue size now is: {rqueue.qsize()}")
            fall_record = []

        # 检测是否摔倒
        is_fall, record = detect_fall(head, foot, hf_distance, last_fall_moment)
        if is_fall:
            last_fall_moment = time.time()
            logging.info(record)
            is_recording = True
            
            # 记录摔倒前1、0.5秒以及摔倒时刻的图片
            fall_record = record_fall_frames(record, USER, frames, fps)
            logging.info("Start Record")
            head = []
            foot = []
        else:
            # 更新头脚间距 hf_distance，仅在当前帧检测到头部和脚部时更新
            if head[-1] is not None and foot[-1] is not None:
                if len(head) == 1 or hf_distance == 0:
                    hf_distance = distance(head[-1], foot[-1])
                else:
                    hf_distance = (hf_distance + distance(head[-1], foot[-1])) / 2
            else :
                hf_distance = 0

        # 将帧转换为JPEG格式的二进制编码
        _, jpg_buffer = cv2.imencode('.jpg', frame)
        frame_data = jpg_buffer.tobytes()
        if fqueue.qsize() > 5:
            fqueue.get()
            fqueue.put(frame_data)
        else:
            fqueue.put(frame_data)

    # 释放视频捕获对象并关闭显示窗口
    cap.release()
    cv2.destroyAllWindows()