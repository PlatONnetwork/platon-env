from typing import List

from platon_env.base.process import Process


class Service:

    def __init__(self, processes: List[Process] = None):
        self.processes: dict = dict()

        if not processes:
            processes = []
        for process in processes:
            self.add_process(process)

    def add_process(self, process: Process):
        """ 将进程添加到服务，进行统一管理
        """
        if self.processes.get(id(process)):
            raise Exception('The process already exists.')

        self.processes[id(process)] = process

    def remove_process(self, name):
        """ 从服务中移除进程
        """
        self.processes.pop(name)

    def get_processes(self, **kwargs):
        """ 通过进程属性，获取进程对象，可以同时匹配多个
        """
        processes = []

        def match(process: Process):
            for key, value in kwargs:
                if process.__getattribute__(key) == value:
                    return process

        for process in self.processes:
            matched = match(process)
            if matched:
                processes.append(matched)

        return processes

    # def show(self, *args, **kwargs):
    #     raise NotImplementedError("process must implement this method")

    def install(self, *args, **kwargs):
        raise NotImplementedError("process must implement this method")

    def uninstall(self, *args, **kwargs):
        raise NotImplementedError("process must implement this method")

    def status(self, *args, **kwargs):
        raise NotImplementedError("process must implement this method")

    def start(self, *args, **kwargs):
        raise NotImplementedError("process must implement this method")

    def restart(self, *args, **kwargs):
        raise NotImplementedError("process must implement this method")

    def stop(self, *args, **kwargs):
        raise NotImplementedError("process must implement this method")
