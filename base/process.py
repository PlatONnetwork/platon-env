from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from base.host import Host


class Process:

    def __init__(self, host: 'Host', name=None, base_dir=None, port=None, pid=None):
        self.host = host
        self.name = name
        self.base_dir = base_dir
        self.port = port
        self.pid = pid

    def check(self, *args, **kwargs):
        pass

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
