import os
from fabric import Connection, Config
from supervisor.supervisor import Supervisor
from utils.md5 import md5
from utils.path import join_path


class Host:

    def __init__(self, ip, username, password, port=22, workdir='platon'):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        config = Config(overrides={'sudo': {'password': password}})
        self.connection = Connection(self.ip, self.username, self.port, config=config, connect_kwargs={'password': password})
        self.supervisor = Supervisor(self)
        self.workdir = join_path(self.ssh('pwd'), workdir)  # todo: 支持home之外的目录
        self.tmpdir = join_path(self.workdir, 'tmp')
        self.ssh(f'mkdir -p {self.tmpdir}')

    def ssh(self, command, sudo=False, warn=True, hide='both', strip=True):
        """
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

    def pid(self, process):
        """ 获取远程主机的进程pid
        """
        return self.ssh(f'ps -ef | grep {process} | grep -v grep | ' + "awk {'print $2'}")

    def is_exist(self, path):
        """ 判断文件是否已存在于远程主机
        """
        return self.ssh(f'test -e {path}', strip=False).ok

    def save_to_file(self, string, path):
        """ 将字符串保存到远程主机
        """
        dir_path, _ = os.path.split(path)
        if dir_path:
            self.ssh(f'mkdir -p {dir_path}')
        self.ssh(rf"echo '{string}' > {path}")

    def put_via_tmp(self, local, remote=None):
        """ 上传文件到远程主机并缓存
        """
        fm = md5(local)
        tmp = join_path(self.tmpdir, fm)
        if not self.is_exist(tmp):
            self.connection.put(local, tmp)
        if not remote:
            return tmp
        path, _ = os.path.split(remote)
        if not self.is_exist(path):
            self.ssh(f'mkdir -p {path}', sudo=True)
        self.ssh(f'cp {tmp} {remote}', sudo=True)
