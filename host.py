import os
import paramiko
from loguru import logger
from paramiko.ssh_exception import SSHException

from supervisor.supervisor import Supervisor
from utils.md5 import md5
from utils.path import join_path


def connect(ip, username='root', password='', port=22):
    transport = paramiko.Transport((ip, port))
    transport.connect(username=username, password=password)
    ssh = paramiko.SSHClient()
    ssh._transport = transport
    sftp = paramiko.SFTPClient.from_transport(transport)
    return ssh, sftp


class Host:

    def __init__(self, ip, username, password, ssh_port=22, base_path='platon'):
        self.ip = ip
        self.username = username
        self.password = password
        self.ssh_port = ssh_port
        self.ssh, self.sftp = connect(self.ip, self.username, self.password, self.ssh_port)
        self.supervisor = Supervisor(self)
        self.base_path = self.get_abs_path(base_path)
        self.tmp_path = join_path(self.base_path, 'tmp')
        self.cmd(f'mkdir -p {self.tmp_path}')

    def pwd(self):
        """ 获取远程主机的当前目录
        """
        outs, _ = self.cmd('pwd')
        return outs[0].strip('\r\n')

    def pid(self, process_name):
        """ 获取远程主机的进程pid
        """
        outs, _ = self.cmd(f'ps -ef | grep {process_name} | grep -v grep' + ' | ' + "awk {'print $2'}")
        return outs

    def is_exist(self, remote_path):
        """ 判断文件是否已存在于远程主机
        """
        outs, _ = self.cmd(f'ls {remote_path}')
        if outs:
            return True
        return False

    def get_abs_path(self, path):
        """ 获取path在远程主机的绝对路径
        """
        if os.path.isabs(path):
            return path
        return join_path(self.pwd(), path)

    def cmd(self, cmd, keys=None, sudo=False, mode='normal'):
        """ 执行远程shell命令
        TODO: 支持多个keys输入

        Args:
            cmd (str): 要执行的命令
            keys (str): 要在执行过程中输入的信息
            sudo (bool): 是否使用root权限执行，在权限不足时使用
            mode: 执行模式，包括’normal‘、’strict‘两种模式，当使用’strict‘模式时，如果命令返回了error信息，则抛出异常
        """
        if sudo:
            cmd = f"sudo -S -p '' {cmd}"
        logger.debug(f'execute command: {cmd}')
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        if keys:
            stdin.write(keys + '\n')
        outs = stdout.readlines()
        errs = stderr.readlines()
        if mode == 'strict' and errs:
            raise SSHException(errs)
        logger.debug(f'command outs: {outs}, errs: {errs}')
        return outs, errs

    def get_file(self, remote_path, local_path):
        """ 下载远程主机的文件
        """
        self.sftp.get(remote_path, local_path)

    def put_file(self, local_path, remote_path=None, sudo=False, mode='normal'):
        """ 上传文件到远程主机
        注意：sftp无法直接上传到权限不足的目录，因此通过缓存进行上传

        Args:
            local_path (str): 本地文件路径
            remote_path (str): 远程文件路径
            sudo (bool): 是否使用root权限上传，在权限不足时使用
            mode (str): 上传模式，包括‘normal’、‘tmp’两种模式，当使用’tmp‘模式时，会对文件进行缓存，建议对需要重复上传的大文件使用
        """
        file_md5 = md5(local_path)
        tmp_file_path = join_path(self.tmp_path, file_md5)
        if not self.is_exist(tmp_file_path):
            self.sftp.put(local_path, tmp_file_path)
        if not remote_path:
            return tmp_file_path
        dir_path, _ = os.path.split(remote_path)
        if not self.is_exist(dir_path):
            self.cmd(f'mkdir -p {dir_path}', sudo=sudo)
        if mode == 'tmp':
            self.cmd(f'cp {tmp_file_path} {remote_path}', self.password, sudo=sudo)
        else:
            self.cmd(f'mv {tmp_file_path} {remote_path}', self.password, sudo=sudo)

    def save_to_file(self, string, remote_path):
        """ 将字符串对象保存到远程主机
        """
        dir_path, _ = os.path.split(remote_path)
        if dir_path:
            self.cmd(f'mkdir -p {dir_path}')
        self.cmd(rf"echo '{string}' > {remote_path}")
