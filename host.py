import os
import configparser
import paramiko
from functools import wraps
from paramiko.ssh_exception import SSHException
from config import HostInfo as HostInfo, Config
from util import md5


failed_msg = r'Host {} do {} failed:{}'
success_msg = r'Host {} do {} success'


def _try_do(func, *args, **kwargs):
    @wraps(func)
    def wrap_func(self, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            return False, failed_msg.format(self.host, func.__name__, e)
        return True, success_msg.format(self.host, func.__name__)
    return wrap_func


def connect(ip, username='root', password='', port=22):
    transport = paramiko.Transport((ip, port))
    transport.connect(username=username, password=password)
    ssh = paramiko.SSHClient()
    ssh._transport = transport
    sftp = paramiko.SFTPClient.from_transport(transport)
    return ssh, sftp


class Host:
    def __init__(self, host_info: HostInfo, config: Config):
        self.host = host_info.host
        self.username = host_info.username
        self.password = host_info.password
        self.ssh_port = host_info.ssh_port
        self.config = config
        # todo：单例化连接
        self.ssh, self.sftp = connect(self.host, self.username, self.password, self.ssh_port)
        self.remote_supervisor_conf = os.path.abspath(os.path.join(self.config.remote_tmp_dir, 'supervisord.conf'))

    @property
    def _pwd(self):
        stdouts = self.run_ssh('pwd')
        return stdouts[0].strip('\r\n')

    def run_ssh(self, cmd, keys: tuple = None):
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        if keys:
            for key in keys:
                stdin.write(key + '\n')
        errs = stderr.readlines()
        if errs:
            raise SSHException({errs})
        outs = stdout.readlines()
        return outs

    @_try_do
    def install_dependency(self):
        self.run_ssh("sudo -S -p '' ntpdate 0.centos.pool.ntp.org", self.password)
        self.run_ssh("sudo -S -p '' apt install llvm g++ libgmp-dev libssl-dev -y", self.password)

    @_try_do
    def install_supervisor(self):
        is_installed = self.run_ssh("apt list | grep supervisor")
        if '[installed]' not in str(is_installed):
            self.run_ssh("sudo -S -p '' apt update", self.password)
            self.run_ssh("sudo -S -p '' apt install -y --reinstall supervisor", self.password)
            template_file = 'supervisor/supervisor_template.conf'
            tmp_file = os.path.join(self.config.local_tmp_dir, self.host, 'supervisord.conf')
            self._fill_supervisor_conf(template_file, tmp_file)
            self._upload_file(tmp_file, self.config.remote_tmp_dir)
        is_running = self.run_ssh("ps -ef | grep supervisord | grep -v grep | awk {'print $2'}")
        if not is_running:
            self.run_ssh("sudo -S -p '' supervisord -c /etc/supervisor/supervisord.conf", self.password)

    def clean_supervisorctl_cfg(self):
        # todo: 精准清理
        self.run_ssh("sudo -S -p '' rm -rf /etc/supervisor/conf.d/n*", self.password)

    def _upload_platon(self, remote_path=None):
        """ 上传platon二进制文件到远程机器，会使用tmp进行缓存
        """
        file_name = 'platon_' + md5(self.config.platon)
        tmp_path = os.path.join(self.config.remote_tmp_dir, file_name)
        if not self._is_file_exist(self.config.platon, self.config.remote_tmp_dir):
            self._upload_file(self.config.platon, tmp_path)
        if remote_path:
            if os.path.isdir(remote_path):
                remote_path = os.path.join(remote_path, 'platon')
        self.run_ssh(f'cp {tmp_path} {remote_path}')

    def _upload_keystore(self, remote_path=None):
        """ 上传keystore文件到远程机器，会使用tmp进行缓存
        """
        # todo: coding
        pass

    def _upload_file(self, file, path):
        local_hash = md5(file)
        path = os.path.join(path, file)
        remote_hash = self.run_ssh(f'md5sum {path}')
        if local_hash is remote_hash:
            return
        self.run_ssh(f'rm {path} && mkdir -p {path}')
        self.sftp.put(file, path)

    def _save_to_file(self, content, file):
        """ 将内容保存为主机上的文件
        """
        path, file = os.path.split(file)
        if path:
            self.run_ssh(f'mkdir -p {path}')
        self.run_ssh(f'echo "{content}" >> {file}')

    def _is_file_exist(self, file, remote_file):
        """ 判断文件是否已存在于主机
        """
        if os.path.isdir(remote_file):
            remote_file = os.path.join(remote_file, '*')
        local_md5 = md5(file)
        remote_md5 = self.run_ssh(f'md5sum {remote_file}')
        if local_md5 in str(remote_md5):
            return True
        return False

    def _fill_supervisor_conf(self, template_file, to_file):
        cfg = configparser.ConfigParser()
        cfg.read(template_file)
        cfg.set('inet_http_server', 'username', self.username)
        cfg.set('inet_http_server', 'password', self.password)
        cfg.set('supervisorctl', 'username', self.username)
        cfg.set('supervisorctl', 'password', self.password)
        with open(to_file, 'w') as f:
            cfg.write(f)