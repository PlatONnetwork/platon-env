import os
from typing import List

from fabric import Connection, Config
from platon_env.base.supervisor.supervisor import Supervisor
from platon_env.utils.md5 import md5
from platon_env.utils.path import join_path
from platon_env.base.process import Process


class Host:
    supervisor: Supervisor = None
    processes: dict = dict()

    def __init__(self,
                 ip: str,
                 username: str,
                 certificate: str = None,
                 password: str = None,
                 port: int = 22,
                 is_superviosr: bool = True,
                 processes: List[Process] = None
                 ):
        """
        初始化远程主机对象并尝试连接，支持免密/密码/证书方式。

        Args:
            ip: IP地址
            username: 用户名
            certificate: 证书
            password: 密码/证书密码
            port: ssh端口
            processes: 要注册的进程
        """
        self.ip = ip
        self.port = port
        self.username = username
        self.certificate = certificate
        self.password = password
        self._connection = None
        self.home_dir = join_path('/home', self.username)
        self.tmp_dir = '.env-tmp'
        self.is_superviosr = is_superviosr
        if self.is_superviosr:
            self.supervisor = Supervisor(self)
            self.prepare()
        if not processes:
            processes = []
        for process in processes:
            self.register(process)

    def __eq__(self, other):
        if self.ip == other.ip and self.username == other.username:
            return True
        return False

    def __hash__(self):
        return hash(id(self))

    @property
    def connection(self):
        """ 单例模式连接到服务器,支持免密/密码/证书方式
        """
        if self._connection and self._connection.is_connected:
            return self._connection

        if self.certificate:
            # todo: 证书方式连接
            config = None
        else:
            config = Config(overrides={'sudo': {'password': self.password}})

        self._connection = Connection(self.ip, self.username, self.port, config=config, connect_kwargs={'password': self.password})
        return self._connection

    def prepare(self):
        """ 主机环境准备
        """
        self.supervisor.install()

    def pid(self, name):
        """ 通过进程名字，获取远程主机的进程号
        """
        return self.ssh(f'ps -ef | grep {name} | grep -v grep | ' + "awk {'print $2'}")

    def ssh(self, command, sudo=False, warn=True, hide='both', strip=True):
        """ 在远程主机上执行ssh命令

        Args:
            command: 需要执行的shell命令行
            sudo: 是否用sudo的方式执行
            warn: 当命令执行失败的时候，以警告的方式打印错误，而不是抛出异常
            hide: 打印错误信息时，需要隐藏的输出内容，包含：out、err、both
            strip: 是否直接返回命令行执行结果，False返回fabric-result对象
        """
        if sudo:
            result = self.connection.sudo(command, warn=warn, hide=hide)
        else:
            result = self.connection.run(command, warn=warn, hide=hide)
        if strip:
            return result.stdout.strip()
        return result

    def file_exist(self, path):
        """ 判断文件是否已存在于远程主机
        """
        return self.ssh(f'test -e {path}', strip=False).ok

    def fast_put(self, local, remote=None, sudo=False):
        """ 使用缓存机制，上传文件到远程主机，以提高上传速度
        # todo: 支持压缩上传
        """
        _md5 = md5(local)
        tmp_file = join_path(self.tmp_dir, _md5)
        if not self.file_exist(self.tmp_dir):
            self.ssh(f'mkdir -p {self.tmp_dir}')
        if not self.file_exist(tmp_file):
            try:
                self.connection.put(local, tmp_file)
            except Exception as e:
                # todo: 按异常类型处理
                raise Exception(f'fast put {local} to {remote} error: {e}')
        if not remote:
            return tmp_file
        path, _ = os.path.split(remote)
        if not self.file_exist(path):
            self.ssh(f'mkdir -p {path}', sudo=sudo)
        self.ssh(f'cp {tmp_file} {remote}', sudo=sudo)

    def write_file(self, content: str, file):
        """ 将文本内容写入远程主机的文件，目前仅支持写入新的文件
        # todo： 支持写入已存在的文件，包括覆盖、追加等方式
        """
        path, _ = os.path.split(file)
        if path:
            self.ssh(f'mkdir -p {path}')

        content = str(content).replace('"', r'\"')
        self.ssh(rf'echo "{content}" > {file}')

    def register(self, process: Process):
        """ 将进程注册到主机对象，以便后续管理和使用
        """
        if self.processes.get(process.name):
            raise Exception()

        self.processes[process.name] = process

    def unregister(self, name):
        """ 通过进程名字，删除远程主机上的进程注册信息
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

    def set_supervisor(self, supervisor: Supervisor):
        self.supervisor = supervisor
