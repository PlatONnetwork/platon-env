import os
from utils.path import join_path

from paramiko.ssh_exception import SSHException

class Supervisor:
    path = '/etc/supervisor'
    conf_file = '/etc/supervisor/supervisor.conf'
    conf_path = '/etc/supervisor/conf.d'
    status_cmd = 'supervisorctl status {}'
    start_cmd = 'supervisorctl start {}'
    restart_cmd = 'supervisorctl restart {}'
    stop_cmd = 'supervisorctl stop {}'
    update_cmd = 'supervisorctl update'

    def __init__(self, host):
        self.host = host

    def _cmd(self, cmd):
        """ 使用严格模式执行supervisor命令
        """
        outs, _ = self.host.cmd(cmd, mode='strict')
        if 'ERROR' in outs:
            raise SSHException(f'{cmd} failed: {outs}')
        return outs

    def status(self, process='') -> bool:
        """ 查看进程状态
        """
        outs = self._cmd(self.status_cmd.format(process))
        if not outs or 'RUNNING' in str(outs):
            return True
        return False

    def start(self, process):
        """ 启动进程
        """
        self._cmd(self.start_cmd.format(process))

    def restart(self, process):
        """ 重启进程
        """
        self._cmd(self.restart_cmd.format(process))

    def stop(self, process):
        """ 停止进程
        """
        self._cmd(self.stop_cmd.format(process))

    def update(self):
        """ 更新进程列表
        """
        self._cmd(self.update_cmd)

    def add(self, process_file):
        """ 指定进程文件来添加进程
        """
        _, file_name = os.path.split(process_file)
        remote_path = join_path(self.conf_path, file_name)
        self.host.put_file(process_file, remote_path, sudo=True)
        self.update()

    def remove(self, process_name):
        """ 删除进程
        """
        process_file = os.path.join(self.conf_path, process_name + '.conf')
        self.host.cmd(f'rm -rf {process_file}', self.host.password, sudo=True)

    def put_config(self):
        """ 上传supervisor的配置文件
        """
        current_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
        local_file = os.path.join(current_path, 'supervisor.conf')
        self.host.put_file(local_file, self.conf_file, sudo=True)

    def install(self):
        """ 安装supervisor
        """
        is_installed, _ = self.host.cmd("apt list | grep supervisor")
        if '[installed]' not in str(is_installed):
            self.host.cmd('apt update', self.host.password, sudo=True)
            self.host.cmd('apt install -y --reinstall supervisor', self.host.password, sudo=True)
            self.put_config()
        pid = self.host.pid('supervisord')
        if not pid:
            self.host.cmd(f'supervisord -c {self.conf_file}', self.host.password, sudo=True)

    def uninstall(self):
        """ 卸载supervisor
        """
        self.host.cmd(f'apt remove supervisor', self.host.password, sudo=True)
