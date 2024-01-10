from multiprocessing import Pool, Queue, Manager, Process
from test_func import func
import importlib
import dill
import time
def testf():
    print(6666)


def import_func_from_file(filepath, func_name):
    spec = importlib.util.spec_from_file_location("module.name", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    func = getattr(module, func_name)
    return func


class MyClass:
    def __init__(self, val) -> None:
        self.data = val

    def my_method(self):
        print("Hello, World!")

def run(queue):
    print(123)
    # print(queue)
    while True:
        print("===")
        i = queue.get()
        print(i)
        time.sleep(1)


if __name__ == '__main__':
    def func(self):
        print("123")
    # obj = MyClass(123)
    # obj.__class__.my_method = func
    # obj.my_method()
    # pool = Pool(processes=4)
    manager = Manager()

    queue = manager.Queue()
    name = manager.Namespace()
    for i in range(20):
        queue.put(None)

    p = Process(target=run, args=[queue,])
    p.start()

    time.sleep(5)

    manager.shutdown()
    p.terminate()
    p.join()
    print(111)

