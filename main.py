from multiprocessing import Process, Queue
import time
import cv2
from ultralytics import YOLO
import json
from flask import Flask, request, abort, send_file, Response
from flask_sock import Sock, Server
import math
import os
import logging


logging.basicConfig(level=logging.WARNING)

logging.getLogger('ultralytics').setLevel(logging.CRITICAL)
logging.getLogger('libpng').setLevel(logging.CRITICAL)

CAMERA = 1

Virtual = 1

user = "u001"

# 检测摔倒的参数
FALL_TIME = 0.15  # 摔倒所用的秒数
INTERVAL = 1.5 # 两次摔倒识别之间的间隔
MAX_DISTANCE = 0.5 # 头部移动距离阈值


# 设置模型
model = YOLO('yolov8n-pose.pt')

def distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def examiner(fqueue, rqueue):
    cap = cv2.VideoCapture(CAMERA)  # 0表示默认摄像头，如果有多个摄像头，可以尝试使用1, 2, 等
    fps = int(cap.get(cv2.CAP_PROP_FPS))  # 获取摄像头的帧率
    if Virtual == 1:
        fps=30

    print("FPS now is: ", fps)

    if_record = 0

    # 摔倒的格式化时间，用于添加记录
    record = ""
    fall_record = []

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

        if success:
            frames.append(frame)
            if len(frames) > int(fps):
                del frames[0]
            # 在该帧上运行YOLOv8推理
            results = model(frame)
            #print(results[0].keypoints.xy[0])
            if len(results[0].keypoints.xy) != 0:
                #print('is person\n')
                #print('num of points: ', len(results[0].keypoints.xy[0]), '\n')
                if len(results[0].keypoints.xy[0]) == 17 and int(results[0].keypoints.xy[0][0][0]) != 0 and int(results[0].keypoints.xy[0][0][1]) != 0 and int(results[0].keypoints.xy[0][16][0]) != 0 and int(results[0].keypoints.xy[0][16][1]) != 0 and int(results[0].keypoints.xy[0][15][0]) != 0 and int(results[0].keypoints.xy[0][15][1]) != 0:
                    #print("ready to detect!!!\n")
                    global move_distance
                    # 将当前头部位置添加到检测区
                    temp = [int(results[0].keypoints.xy[0][0][0]), int(results[0].keypoints.xy[0][0][1])]

                    head.append(temp)

                    # 将当前脚部位置添加到检测区
                    temp1 = [int(results[0].keypoints.xy[0][-2][0]), int(results[0].keypoints.xy[0][-2][0])]
                    temp2 = [int(results[0].keypoints.xy[0][-1][0]), int(results[0].keypoints.xy[0][-1][1])]

                    foot.append(max(temp1, temp2, key=lambda x: distance(x, temp)))

                    if len(head) > int(FALL_TIME * fps):
                        del head[0]
                        del foot[0]

                    #print('original hf_distance: ', hf_distance, '\n')
                    move_distance = abs(distance(head[0], head[-1]))
                    #print('head move distance: ', move_distance, '\n')

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


                        # time.sleep(1.5)
                        move_distance = 0
                        head = []
                        foot = []
                    else:
                        # 更新头脚间距用于对照
                        if len(head) == 1:
                            hf_distance = distance(head[0], foot[0])
                        else:
                            hf_distance = (hf_distance + distance(head[-1], foot[-1])) / 2
                        #print('updated hf_distance', hf_distance, '\n')


            # 将帧转换为JPEG格式的二进制编码
            _, jpg_buffer = cv2.imencode('.jpg', frame)


            #print("frame got")
            # 将二进制编码转换为bytes类型
            frame_data = jpg_buffer.tobytes()


            # 发送帧到队列
            if fqueue.qsize() > 5:
                fqueue.get()
                fqueue.put(frame_data)
            else:
                fqueue.put(frame_data)

            # 在帧上可视化结果
            annotated_frame = results[0].plot()

            # 显示带注释的帧
            cv2.imshow("YOLOv8推理", annotated_frame)

            # 如果按下'q'则中断循环

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # 如果视频结束则中断循环
            print("end")
            break

    # 释放视频捕获对象并关闭显示窗口
    cap.release()
    cv2.destroyAllWindows()


def recorder(rqueue):
    while True:
        record = rqueue.get()

        print("\033[94mStart Write\033[0m")

        time = record[0]
        user = record[1]

        cv2.imwrite("./picture/01.jpg", record[2])
        cv2.imwrite("./picture/02.jpg", record[3])
        cv2.imwrite("./picture/03.jpg", record[4])
        cv2.imwrite("./picture/04.jpg", record[5])
        print("Pictures written")

        for i in range(4):
            os.rename(f"./picture/0{i+1}.jpg", f"./picture/{user}-{time}-0{i+1}.jpg")
        #f"./picture/{user}-{time}-02.jpg"

        data = {
            "record": time,
            "user": user,
            "is_clicked": 0
        }

        # asyncio.run(write_to_file("fall record.json", data))

        with open("fall record.json", "r+") as f:
            rdata = json.load(f)
            rdata.insert(0, data)
            f.seek(0, 0)
            json.dump(rdata, f, indent=4)


def server(fqueue):
    app = Flask(__name__)
    sock = Sock(app)

    @sock.route('/connect')
    def connect(ws: Server):
        # cap = cv2.VideoCapture(CAMERA)
        # while cap.isOpened():
        #     success, frame = cap.read()
        #     if success:
        # 将帧转换为JPEG格式的二进制编码
        while True:
            frame = fqueue.get()
        #         _, jpg_buffer = cv2.imencode('.jpg', frame)
        #
        #         # 将二进制编码转换为bytes类型
        #         frame = jpg_buffer.tobytes()
            ws.send(frame)

    @app.route('/checkall', methods=["POST"])
    def checkall():
        with open('fall record.json', 'r+') as f:
            data = json.load(f)
            return data

    @app.route('/update', methods=["POST"])
    def update():
        # 获取要更新的数据项
        record = json.loads(request.data)
        record0 = record["record"]
        user = record["user"]

        with open("fall record.json", 'r+') as f:
            data = json.load(f)
            for r in data:
                if r["record"] == record0 and r["user"] == user:
                    r["is_clicked"] = 1
                    f.seek(0, 0)
                    json.dump(data, f, indent=4)
        return {}


    @app.route('/download/<filename>', methods=["POST", "GET"])
    def download(filename):
        # 如果没有提供文件名，返回400错误
        if not filename:
            abort(400, description="Filename is required")

        # 构造文件路径（请根据需要修改）
        file_path = os.path.join("./picture", filename)

        try:
            # 发送文件
            return send_file(file_path, as_attachment=True)

        except FileNotFoundError:
            # 如果文件未找到，返回404错误
            abort(404, description="File not found")


    app.run(port=8088)





Cameraon = 1
Serveron = 1
Recorderon = 1


if __name__ == "__main__":
    fqueue = Queue()
    rqueue = Queue()


    producer_process = Process(target=examiner, args=(fqueue, rqueue))

    consumer_process = Process(target=server, args=(fqueue,))

    recorder_process = Process(target=recorder, args=(rqueue,))

    if Cameraon == 1:
        producer_process.start()
    if Serveron == 1:
        consumer_process.start()
    if Recorderon == 1:
        recorder_process.start()

    if Cameraon == 1:
        producer_process.join()
    if Serveron == 1:
        consumer_process.join()
