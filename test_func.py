import multiprocessing
import time
# import dill
from threading import Lock

val = 0
lock = Lock()

def func(queue=None):
    print(lock)
    # global val
    # val += 1
    # obj = queue.get()
    # print(333)
    # print(dill.loads(obj))
    # print(444)
    # # f()
    # print(f"进程ID：{multiprocessing.current_process().pid}，val：{val}")
    # time.sleep(0.01)

