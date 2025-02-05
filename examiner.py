import cv2
import time
import math
from ultralytics import YOLO

# 摄像头和用户配置
CAMERA = 0
Virtual = 1
user = "u001"

# 检测摔倒的参数
FALL_TIME = 0.15  # 摔倒所用的秒数
INTERVAL = 1.5  # 两次摔倒识别之间的间隔
MAX_DISTANCE = 0.5  # 头部移动距离阈值

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
    if any(int(coord) == 0 for coord in [
        kpts[0][0], kpts[0][1],
        kpts[15][0], kpts[15][1],
        kpts[16][0], kpts[16][1]
    ]):
        return False
    return True

def examiner(fqueue, rqueue):
    """视频帧处理函数"""
    cap = cv2.VideoCapture(CAMERA)  # 打开摄像头
    fps = int(cap.get(cv2.CAP_PROP_FPS))  # 获取摄像头的帧率
    if Virtual == 1:
        fps = 30

    print("FPS now is: ", fps)

    if_record = 0

    # 摔倒的格式化时间，用于添加记录
    record = ""
    fall_record = []
    # 头部和脚部检测区列表
    head = []
    foot = []
    frames = []

    hf_distance = 0
    fall_moment = 0

    # 遍历视频帧
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("end")
            break

        frames.append(frame)
        if len(frames) > int(fps):
            del frames[0]

        results = model(frame)
        
        # 先显示图像
        if len(results) > 0:
            annotated_frame = results[0].plot()
        else:
            annotated_frame = frame
        cv2.imshow("YOLO推理", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        if not validate_results(results):
            continue

        xy = results[0].keypoints.xy
        kpts = xy[0].cpu().numpy()

        # 将当前头部位置添加到检测区
        temp = [int(kpts[0][0]), int(kpts[0][1])]

        head.append(temp)

        # 将当前脚部位置添加到检测区
        temp1 = [int(kpts[-2][0]), int(kpts[-2][0])]
        temp2 = [int(kpts[-1][0]), int(kpts[-1][1])]

        foot.append(max(temp1, temp2, key=lambda x: distance(x, temp)))

        if len(head) > int(FALL_TIME * fps):
            del head[0]
            del foot[0]

        move_distance = abs(distance(head[0], head[-1]))

        if if_record == 1 and time.time()-fall_moment >= 0.5:
            if_record = 0
            fall_record.append(frame)
            rqueue.put(fall_record)
            print("\033[93mFinish Record\033[0m")
            print("Queue size now is: ", rqueue.qsize())
            fall_record = []

        # 检测是否摔倒
        if move_distance >= 0.5 * hf_distance and time.time() - fall_moment >= 1.5 and hf_distance != 0:
            print("\033[91mDETECTED FALLING!!!!!\033[0m")
            fall_moment = time.time()
            record = time.strftime("%Y%m%d-%H-%M-%S", time.localtime(fall_moment))
            print(record)
            if_record = 1
            # 记录摔倒前1、0.5秒以及摔倒时刻的图片
            fall_record.append(record)
            fall_record.append(user)
            fall_record.append(frames[0])
            fall_record.append(frames[fps//2])
            fall_record.append(frame)
            print("\033[92mStart Record\033[0m")
            move_distance = 0
            head = []
            foot = []
        else:
            # 更新头脚间距用于对照
            if len(head) == 1:
                hf_distance = distance(head[0], foot[0])
            else:
                hf_distance = (hf_distance + distance(head[-1], foot[-1])) / 2

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