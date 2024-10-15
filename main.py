from multiprocessing import Process, Queue
import sys
from examiner import examiner
from recorder import recorder
from server import server
import logging

logging.basicConfig(level=logging.WARNING)
logging.getLogger('ultralytics').setLevel(logging.CRITICAL)
logging.getLogger('libpng').setLevel(logging.CRITICAL)

# 是否开启摄像头、服务器和记录器
Cameraon = True
Serveron = True
Recorderon = True

if __name__ == "__main__":
    fqueue = Queue()
    rqueue = Queue()

    producer_process = Process(target=examiner, args=(fqueue, rqueue))
    consumer_process = Process(target=server, args=(fqueue,))
    recorder_process = Process(target=recorder, args=(rqueue,))

    if Cameraon:
        producer_process.start()
    if Serveron:
        consumer_process.start()
    if Recorderon:
        recorder_process.start()

    if Cameraon:
        producer_process.join()
    if Serveron:
        consumer_process.join()