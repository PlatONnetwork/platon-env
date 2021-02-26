import os
import configparser
import paramiko
from functools import wraps
from config import Host as HostInfo, Config
from util import md5

failed_msg = r'Host {} do {} failed:{}'
success_msg = r'Host {} do {} success'


def connect(ip, username='root', password='', port=22):
    transport = paramiko.Transport((ip, port))
    transport.connect(username=username, password=password)
    ssh = paramiko.SSHClient()
    ssh._transport = transport
    sftp = paramiko.SFTPClient.from_transport(transport)
    return ssh, sftp


def _try_do(func, *args, **kwargs):
    @wraps(func)
    def wrap_func(self, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            return False, failed_msg.format(self.host, func.__name__, e)
        return True, success_msg.format(self.host, func.__name__)
    return wrap_func


class Host:
    def __init__(self, host_info: HostInfo, config: Config):
        self.host = host_info.host
        self.username = host_info.username
        self.password = host_info.password
        self.ssh_port = host_info.ssh_port
        self.config = config
        self.ssh, self.sftp = connect(self.host, self.username, self.password, self.ssh_port)
        self.remote_supervisor_conf = os.path.abspath(os.path.join(self.config.remote_tmp_dir, 'supervisord.conf'))

    def run_ssh(self, cmd, keys: tuple = None):
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        if keys:
            for key in keys:
                stdin.write(key + '\n')
        if stderr:
            raise Exception(f'exec command error: {stderr}')
        outs = stdout.readlines()
        return outs

    def upload_file(self, file_path, remote_path):
        local_hash = md5(file_path)
        remote_hash = self.run_ssh(f'')
        if local_hash is remote_hash:
            return
        self.run_ssh(f'rm {remote_path} && mkdir -p {remote_path}')
        self.sftp.put(file_path, remote_path)

    def save_file(self, string, remote_file_path):
        """ 保存内容到远程文件
        """
        path, file = os.path.split(remote_file_path)
        if path:
            self.run_ssh(f'mkdir -p {path}')
        self.run_ssh(f'echo "{string}" >> {remote_file_path}')

    def file_exist(self, file_path, remote_path):
        """ 判断文件是否已存在于远端
        """
        local_md5 = md5(file_path)
        remote_md5 = self.run_ssh(f'md5sum {remote_path}')
        if local_md5 in str(remote_md5):
            platon_name = f'platon_{local_md5}'


    def upload_platon(self):
        """ 上传platon二进制文件到远程机器，会使用tmp进行缓存
        """
        md5(self.config.)
        self.upload_file(self.config.platon, self.config.remote_tmp_dir)

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
            self.__fill_supervisor_conf(template_file, tmp_file)
            self.upload_file(tmp_file, self.config.remote_tmp_dir)
        is_running = self.run_ssh("ps -ef | grep supervisord | grep -v grep | awk {'print $2'}")
        if not is_running:
            self.run_ssh("sudo -S -p '' supervisord -c /etc/supervisor/supervisord.conf", self.password)

    def __fill_supervisor_conf(self, template_file, to_file):
        cfg = configparser.ConfigParser()
        cfg.read(template_file)
        cfg.set('inet_http_server', 'username', self.username)
        cfg.set('inet_http_server', 'password', self.password)
        cfg.set('supervisorctl', 'username', self.username)
        cfg.set('supervisorctl', 'password', self.password)
        with open(to_file, 'w') as f:
            cfg.write(f)

    def clean_supervisorctl_cfg(self):
        self.run_ssh("sudo -S -p '' rm -rf /etc/supervisor/conf.d/n*", self.password)

    @property
    def pwd(self):
        stdouts = self.run_ssh('pwd')
        return stdouts[0].strip('\r\n')