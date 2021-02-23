import os
import configparser
from functools import wraps
from funcs.connect import connect_linux
from tools.platon_deploy import config
from tools.platon_deploy.util import run_ssh

failed_msg = r'Host {} do {} failed:{}'
success_msg = r'Host {} do {} success'


class Host:
    def __init__(self, host_info):
        self.host = host_info['host']
        self.username = host_info['username']
        self.password = host_info['password']
        self.port = host_info.get('sshport', 22)
        self.ssh, self.sftp, self.t = connect_linux(self.host, self.username, self.password, self.port)
        self.remote_supervisor_conf = os.path.abspath(os.path.join(config.REMOTE_SUPERVISOR_TMP_DIR, 'supervisord.conf'))

    def run_ssh(self, cmd, password=None):
            return run_ssh(self.ssh, cmd, password)

    def _try_do(self, func, *args, **kwargs):
        @wraps(func)
        def wrap_func(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                return False, failed_msg.format(self.host, func.__name__, e)
            return True, success_msg.format(self.host, func.__name__)
        return wrap_func

    @_try_do
    def upload_files(self, res_hash):
        ls = self.run_ssh(f'cd {config.REMOTE_RESOURCE_TMP_DIR}; ls')
        file_name = res_hash + '.tar.gz'
        local_path = os.path.join(config.TMP_DIR, file_name)
        remote_path = os.path.join(config.REMOTE_RESOURCE_TMP_DIR, file_name)
        if (file_name + '\n') in ls:
            return True, 'files is existed, need not upload.'
        self.run_ssh(f'rm -rf {config.REMOTE_RESOURCE_TMP_DIR}; mkdir -p {config.REMOTE_RESOURCE_TMP_DIR}')
        self.sftp.put(local_path, remote_path)
        self.run_ssh(f'tar -xzvf {remote_path} -C {config.REMOTE_RESOURCE_TMP_DIR}')

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
        cfg.read(self.cfg.supervisor_file)
        cfg.set('inet_http_server', 'username', self.username)
        cfg.set('inet_http_server', 'password', self.password)
        cfg.set('supervisorctl', 'username', self.username)
        cfg.set('supervisorctl', 'password', self.password)
        with open(sup_tmp, 'w') as file:
            cfg.write(file)

    def clean_supervisor_cfg(self):
        self.run_ssh("sudo -S -p '' rm -rf /etc/supervisor/conf.d/node-*", self.password)