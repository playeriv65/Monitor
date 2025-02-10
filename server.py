import json
import os
from flask import Flask, request, abort, send_file
from flask_sock import Sock, Server
from config import PICTURE_DIR, FALL_RECORD_FILE, PORT

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
        with open(FALL_RECORD_FILE, 'r+') as f:
            data = json.load(f)
            return data

    @app.route('/update', methods=["POST"])
    def update():
        # 获取要更新的数据项
        record = json.loads(request.data)
        record0 = record["record"]
        user = record["user"]

        with open(FALL_RECORD_FILE, 'r+') as f:
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
        file_path = os.path.join(PICTURE_DIR, filename)

        try:
            # 发送文件
            return send_file(file_path, as_attachment=True)

        except FileNotFoundError:
            # 如果文件未找到，返回404错误
            abort(404, description="File not found")

    app.run(port=PORT)