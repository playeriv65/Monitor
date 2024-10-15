import cv2
import time
import math
import torch
from ultralytics import YOLO

# 摄像头和用户配置
CAMERA = 0  # 摄像头编号
VIRTUAL = 0  # 是否使用虚拟摄像头
VIRTUAL_FPS = 30  # 虚拟摄像头的帧率
user = "u001"

# 检测摔倒的参数
FALL_TIME = 0.15  # 摔倒所用的秒数
INTERVAL = 1.5  # 两次摔倒识别之间的间隔
MAX_DISTANCE = 0.5  # 头部移动距离阈值
P_MIN = 0.2 # 最小置信度
MODEL_PATH = "yolo11n-pose.pt"  # 模型路径

# 设置模型
model = YOLO(MODEL_PATH)

def distance(a, b):
    """计算两点之间的欧几里得距离"""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def update_positions(head, foot, keypoints_xy, keypoints_conf, fps):
    """更新头部和脚部位置"""
    head_valid = 0 if keypoints_conf[0].item() < P_MIN else 1
    foot_valid_1 = 0 if keypoints_conf[15].item() < P_MIN else 1
    foot_valid_2 = 0 if keypoints_conf[16].item() < P_MIN else 1

    # 更新头部位置
    if head_valid:
        head_position = [keypoints_xy[0][0].item(), keypoints_xy[0][1].item()]
        head.append(head_position)
    else:
        head.append(None)  # 使用 None 作为占位符

    # 更新脚部位置
    if foot_valid_1:
        foot_position_1 = [keypoints_xy[15][0].item(), keypoints_xy[15][1].item()]
        foot.append(foot_position_1)
    else:
        foot.append(None)

    if foot_valid_2:
        foot_position_2 = [keypoints_xy[16][0].item(), keypoints_xy[16][1].item()]
        foot.append(foot_position_2)
    else:
        foot.append(None)

    # 删除过期的头部和脚部位置
    while len(head) > FALL_TIME * fps:
        del head[0]
    
    while len(foot) > FALL_TIME * fps:
        del foot[0]

def detect_fall(head, foot, hf_distance, fall_moment, frames, frame, fps):
    """检测是否摔倒"""
    if head[0] is not None and head[-1] is not None:
        move_distance = abs(distance(head[0], head[-1]))
    else:
        move_distance = 0  # 如果头部位置消失，则移动距离为0

    if move_distance >= MAX_DISTANCE * hf_distance and time.time() - fall_moment >= INTERVAL and hf_distance != 0:
        print("\033[91mDETECTED FALLING!!!!!\033[0m")
        fall_moment = time.time()
        record = time.strftime("%Y%m%d-%H-%M-%S", time.localtime(fall_moment))
        print(record)
        fall_record = [record, user, frames[0], frames[fps//2], frame]
        print("\033[92mStart Record\033[0m")
        move_distance = 0
        head.clear()
        foot.clear()
        return fall_record, fall_moment, True
    else:
        # 更新头脚间距用于对照
        if len(head) == 1:
            hf_distance = distance(head[0], foot[0])
        else:
            hf_distance = (hf_distance + distance(head[-1], foot[-1])) / 2
        return None, fall_moment, False, hf_distance

def save_fall_record(fall_record, rqueue):
    """保存摔倒记录"""
    rqueue.put(fall_record)
    print("\033[93mFinish Record\033[0m")

def examiner(fqueue, rqueue):
    """视频帧处理函数"""
    cap = cv2.VideoCapture(CAMERA)  # 打开摄像头
    fps = VIRTUAL_FPS if VIRTUAL else cap.get(cv2.CAP_PROP_FPS)  # 获取帧率
    print("FPS now is: ", fps)

    if_record = 0

    # 初始化头部和脚部检测区列表
    head = []
    foot = []
    frames = []

    hf_distance = 0
    fall_moment = 0

    # 遍历视频帧
    while cap.isOpened():
        # 从视频中读取一帧
        success, frame = cap.read()
        if not success:
            # 如果视频结束则中断循环
            print("end")
            break
        results = model(frame)
        frames.append(frame)
        if len(frames) > fps:
            del frames[0]

        # 将帧转换为JPEG格式的二进制编码
        _, jpg_buffer = cv2.imencode('.jpg', frame)
        frame_data = jpg_buffer.tobytes()
        # 发送帧到队列
        if fqueue.qsize() > 5:
            fqueue.get()
            fqueue.put(frame_data)
        else:
            fqueue.put(frame_data)
        annotated_frame = results[0].plot() # 在帧上可视化结果
        cv2.imshow("YOLOv8推理", annotated_frame) # 显示带注释的帧
        if cv2.waitKey(1) & 0xFF == ord("q"): # 如果按下'q'则中断循环
            break
        
        if results[0].keypoints.xy[0].size() != torch.Size([17, 2]):
            continue
        keypoints_xy = results[0].keypoints.xy[0]  # 获取关键点坐标
        keypoints_conf = results[0].keypoints.conf[0]  # 获取关键点置信度

        # 更新头部和脚部位置
        update_positions(head, foot, keypoints_xy, keypoints_conf, fps)

        # 摔倒检测与记录
        fall_record, fall_moment, detected, hf_distance = detect_fall(head, foot, hf_distance, fall_moment, frames, frame, fps)
        if detected:
            save_fall_record(fall_record, rqueue)
            if_record = 1
        else:
            if if_record == 1 and time.time() - fall_moment >= 0.5:
                if_record = 0
                save_fall_record(fall_record, rqueue)
                fall_record = []


    # 释放视频捕获对象并关闭显示窗口
    cap.release()
    cv2.destroyAllWindows()