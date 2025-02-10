import cv2
import json
import os
import logging
from config import PICTURE_DIR, FALL_RECORD_FILE

def recorder(rqueue):
    while True:
        record = rqueue.get()

        logging.info("\033[94mStart Write\033[0m")

        time = record[0]
        user = record[1]
        
        for i in range(4):
            filename = f"{user}-{time}-{(i+1):03d}.jpg"
            cv2.imwrite(os.path.join(PICTURE_DIR, filename), record[i+2])
        
        logging.info("Pictures written")  # 记录日志

        data = {
            "record": time,
            "user": user,
            "is_clicked": 0
        }

        with open(FALL_RECORD_FILE, "r+") as f:
            rdata = json.load(f)
            rdata.insert(0, data)
            f.seek(0, 0)
            json.dump(rdata, f, indent=4)