import os
import configparser
import paramiko
from functools import wraps
from config import Host as HostInfo, Config
from util import file_hash

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
        self.ssh, self.sftp = connect(self.host, self.username, self.password, self.ssh_port)
        self.remote_supervisor_conf = os.path.abspath(os.path.join(self.config.remote_tmp_dir, 'supervisord.conf'))

    def run_ssh(self, cmd, password=None):
        # TODO: 支持多次输入密码
        stdin, stdout, _ = self.ssh.exec_command(cmd)
        if password:
            stdin.write(password + '\n')
        stdouts = stdout.readlines()
        return stdouts

    def upload_file(self, file_path, remote_path):
        local_hash = file_hash(file_path)
        remote_hash = self.run_ssh(f'')
        if local_hash is remote_hash:
            return
        self.run_ssh(f'rm {remote_path} && mkdir -p {remote_path}')
        self.sftp.put(file_path, remote_path)

    def __upload_remote_tmp(self):
        self.upload_file(self.config.platon, self.config.remote_tmp_dir)


    @_try_do
    def install_dependency(self):
        self.run_ssh("sudo -S -p '' ntpdate 0.centos.pool.ntp.org", self.password)
        self.run_ssh("sudo -S -p '' apt install llvm g++ libgmp-dev libssl-dev -y", self.password)

    @_try_do
    def install_supervisor(self):
        result = self.run_ssh("sudo -S -p '' supervisorctl stop test-node", self.password)
        if len(result) == 0 or 'test-node' not in result[0]:
            tmp_dir = os.path.join(self.cfg.server_tmp, self.host)
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            tmp = os.path.join(tmp_dir, 'supervisord.conf')
            self.__rewrite_supervisor_conf(tmp)
            self.run_ssh(f'mkdir -p {self.remote_supervisor_conf}')
            self.sftp.put(tmp, self.remote_supervisor_conf)
            supervisor_pid_str = self.run_ssh("ps -ef | grep supervisord | grep -v grep | awk {'print $2'}")
            if len(supervisor_pid_str) > 0:
                self.__reload_supervisor(supervisor_pid_str)
            else:
                self.run_ssh("sudo -S -p '' apt update", self.password)
                self.run_ssh("sudo -S -p '' apt install -y supervisor", self.password)
                self.run_ssh(f"sudo -S -p '' cp {self.remote_supervisor_conf} /etc/supervisor/", self.password)
                supervisor_pid_str = self.run_ssh("ps -ef | grep supervisord | grep -v grep | awk {'print $2'}")
                if len(supervisor_pid_str) > 0:
                    self.__reload_supervisor(supervisor_pid_str)
                else:
                    self.run_ssh("sudo -S -p '' /etc/init.d/supervisor start", self.password)

    def __reload_supervisor(self, supervisor_pid_str):
        supervisor_pid = supervisor_pid_str[0].strip('\n')
        self.run_ssh(f"sudo -S -p '' kill {supervisor_pid}", self.password)
        self.run_ssh("sudo -S -p '' killall supervisord", self.password)
        self.run_ssh("sudo -S -p '' sudo apt remove supervisor -y", self.password)
        self.run_ssh("sudo -S -p '' apt update", self.password)
        self.run_ssh("sudo -S -p '' apt install -y supervisor", self.password)
        self.run_ssh(f"sudo -S -p '' cp {self.remote_supervisor_conf} /etc/supervisor/", self.password)
        self.run_ssh("sudo -S -p '' /etc/init.d/supervisor start", self.password)

    def __rewrite_supervisor_conf(self, sup_tmp):
        cfg = configparser.ConfigParser()
        cfg.read(self.config.d)
        cfg.set('inet_http_server', 'username', self.username)
        cfg.set('inet_http_server', 'password', self.password)
        cfg.set('supervisorctl', 'username', self.username)
        cfg.set('supervisorctl', 'password', self.password)
        with open(sup_tmp, 'w') as file:
            cfg.write(file)

    def clean_supervisor_cfg(self):
        self.run_ssh("sudo -S -p '' rm -rf /etc/supervisor/conf.d/node-*", self.password)
