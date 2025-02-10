from multiprocessing import Process, Queue
import sys
from examiner import examiner
from recorder import recorder
from server import server
import logging
from config import CAMERA_ON, SERVER_ON, RECORDER_ON

logging.basicConfig(level=logging.WARNING)
logging.getLogger('ultralytics').setLevel(logging.CRITICAL)
logging.getLogger('libpng').setLevel(logging.CRITICAL)

if __name__ == "__main__":
    fqueue = Queue()
    rqueue = Queue()

    producer_process = Process(target=examiner, args=(fqueue, rqueue))
    consumer_process = Process(target=server, args=(fqueue,))
    recorder_process = Process(target=recorder, args=(rqueue,))

    if CAMERA_ON:
        producer_process.start()
    if SERVER_ON:
        consumer_process.start()
    if RECORDER_ON:
        recorder_process.start()

    if CAMERA_ON:
        producer_process.join()
    if SERVER_ON:
        consumer_process.join()