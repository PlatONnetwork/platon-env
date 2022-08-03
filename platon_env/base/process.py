import os
from typing import TYPE_CHECKING

from platon_env.utils import join_path

if TYPE_CHECKING:
    from platon_env.base.host import Host


class Process:

    def __init__(self, host: 'Host', port=None, pid=None, name=None, base_dir=''):
        self.host = host
        self.port = port
        self.pid = pid
        self.name = name
        self.base_dir = base_dir
        if self.base_dir and not os.path.isabs(self.base_dir):
            self.base_dir = join_path(self.host.home_dir, self.base_dir)

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
