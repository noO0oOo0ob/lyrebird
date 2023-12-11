from multiprocessing import Pool, Queue, Manager
from test_func import func
import importlib
import dill

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


if __name__ == '__main__':
    def func(self):
        print("123")
    obj = MyClass(123)
    obj.__class__.my_method = func
    obj.my_method()
    # pool = Pool(processes=4)
    # manager = Manager()
    # manager2 = Manager()
    # print(manager == manager2)
    # print(manager is manager2)
    # print(manager._process.pid)
    # print(manager2._process.pid)

    # queue = manager.Queue()
    # aa = import_func_from_file("/Users/sheng/workCode/lyrebird/test_func2.py", "func2")
    # aa = MyClass(321)
    # print(aa)
    # try:
    #     aa = dill.dumps(aa)
    # except Exception as e:
    #     print(e)
    # # print(aa)
    # # queue.put(123)
    # for i in range(4):
    #     queue.put(aa)
    # print("start")
    # for i in range(4):
    #     pool.apply_async(func, args=(queue,))
    # # for i in range(3):
    # #     pool.map(func, range(4))
    # print("end")
    # pool.close()
    # pool.join()
    # for i in range(3):
    #     pool.map(func, range(4))

