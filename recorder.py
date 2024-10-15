import cv2
import json
import os

RECORD_PATH = "./picture/"
RECORD_NUM = 4

def recorder(rqueue):
    """
    根据队列记录摔倒事件，并保存一定数量的图片

    Args:
        rqueue: 用于记录摔倒事件的队列
    """
    
    while True:
        record = rqueue.get() # 阻塞，直到有数据

        print("\033[94mStart Write\033[0m")

        time = record[0]
        user = record[1]

        for i in range(RECORD_NUM):
            filepath = os.path.join(RECORD_PATH, f"{user}-{time}-{i+1:04}.jpg") # 补前导零至4位
            cv2.imwrite(filepath, record[i+2])
        print("Pictures written")

        data = {
            "record": time,
            "user": user,
            "is_clicked": 0
        }

        with open("fall record.json", "r+") as f:
            rdata = json.load(f)
            rdata.insert(0, data)
            f.seek(0, 0)
            json.dump(rdata, f, indent=4)