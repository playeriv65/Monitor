import cv2
import json
import os

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

        # asyncio.run(write_to_file("fall_record.json", data))

        with open("fall_record.json", "r+") as f:
            rdata = json.load(f)
            rdata.insert(0, data)
            f.seek(0, 0)
            json.dump(rdata, f, indent=4)