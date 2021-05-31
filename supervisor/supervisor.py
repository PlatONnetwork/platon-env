import os
from utils.path import join_path

from paramiko.ssh_exception import SSHException

class Supervisor:
    base_path = '/etc/supervisor'
    config_file = '/etc/supervisor/supervisor.conf'
    process_config_path = '/etc/supervisor/conf.d'
    status_command = 'supervisorctl status {}'
    start_command = 'supervisorctl start {}'
    restart_command = 'supervisorctl restart {}'
    stop_command = 'supervisorctl stop {}'
    update_command = 'supervisorctl update'

    def __init__(self, host):
        self.host = host

    def _cmd(self, cmd):
        """ 使用严格模式执行supervisor命令
        """
        outs, _ = self.host.cmd(cmd, mode='strict')
        if 'ERROR' in outs:
            raise SSHException(f'{cmd} failed: {outs}')
        return outs

    def add(self, process_file):
        """ 指定进程文件来添加进程
        """
        _, file_name = os.path.split(process_file)
        remote_path = join_path(self.process_config_path, file_name)
        self.host.put_file(process_file, remote_path, sudo=True)
        self.update()

    def add_via_node(self, node):
        """ 在远程主机生成节点的supervisor配置文件
        """
        program = f'[program:{node.name}]\n'
        bls_key_cmd = f'--cbft.blskey {node.bls_prikey_file} ' if node.bls_prikey else ''
        command = (f'command={node.platon} --identity {node.name} '
                   f'--datadir {node.data_dir} '
                   f'--port {node.p2p_port} '
                   f'--nodekey {node.node_key_file} '
                   f'{bls_key_cmd}'
                   f'{node.start_options} \n')
        setting = '\n'.join(['numprocs=1', 'autostart=false', 'startsecs=1', 'startretries=3', 'autorestart=unexpected',
                             'exitcode=0', 'stopsignal=TERM', 'stopwaitsecs=10', 'redirect_stderr=true',
                             'stdout_logfile_maxbytes=200MB', 'stdout_logfile_backups=20',
                             f'stdout_logfile={node.log_file}'])
        configs = program + command + setting
        self.host.cmd(f"sh -c 'echo \"{configs}\" > {node.supervisorctl_file}'", node.host.password, sudo=True)
        self.host.supervisor.update()

    def remove(self, process_name):
        """ 删除进程
        """
        process_file = os.path.join(self.process_config_path, process_name + '.conf')
        self.host.cmd(f'rm -rf {process_file}', self.host.password, sudo=True)

    def status(self, process='') -> bool:
        """ 查看进程状态
        """
        outs = self._cmd(self.status_command.format(process))
        if not outs or 'RUNNING' in str(outs):
            return True
        return False

    def update(self):
        """ 更新进程列表
        """
        self._cmd(self.update_command)

    def start(self, process):
        """ 启动进程
        """
        self._cmd(self.start_command.format(process))

    def restart(self, process):
        """ 重启进程
        """
        self._cmd(self.restart_command.format(process))

    def stop(self, process):
        """ 停止进程
        """
        self._cmd(self.stop_command.format(process))

    def upload_config(self, config_file=None):
        """ 上传supervisor的配置文件
        """
        if not config_file:
            current_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
            config_file = os.path.join(current_path, 'supervisor.conf')
        self.host.put_file(config_file, self.config_file, sudo=True)

    def install(self):
        """ 安装supervisor
        """
        is_installed, _ = self.host.cmd("apt list | grep supervisor")
        if '[installed]' not in str(is_installed):
            self.host.cmd('apt update', self.host.password, sudo=True)
            self.host.cmd('apt install -y --reinstall supervisor', self.host.password, sudo=True)
            self.upload_config()
        pid = self.host.pid('supervisord')
        if not pid:
            self.host.cmd(f'supervisord -c {self.config_file}', self.host.password, sudo=True)

    def uninstall(self):
        """ 卸载supervisor
        """
        self.host.cmd(f'apt remove supervisor', self.host.password, sudo=True)
