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

    def add(self, process_file):
        """ 指定进程文件来添加进程
        """
        _, file_name = os.path.split(process_file)
        remote_path = join_path(self.process_config_path, file_name)
        self.host.put_via_tmp(process_file, remote_path)
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
        self.host.ssh(f"sh -c 'echo \"{configs}\" > {node.supervisorctl_file}'", sudo=True)
        self.host.supervisor.update()

    def remove(self, process_name):
        """ 删除进程
        """
        process_file = os.path.join(self.process_config_path, process_name + '.conf')
        self.host.ssh(f'rm -rf {process_file}', sudo=True)

    def status(self, process='') -> bool:
        """ 查看进程状态
        """
        outs = self.host.ssh(self.status_command.format(process))
        if not outs or 'RUNNING' in str(outs):
            return True
        return False

    def update(self):
        """ 更新进程列表
        """
        self.host.connection(self.update_command)

    def start(self, process):
        """ 启动进程
        """
        self.host.connection(self.start_command.format(process))

    def restart(self, process):
        """ 重启进程
        """
        self.host.connection(self.restart_command.format(process))

    def stop(self, process):
        """ 停止进程
        """
        self.host.connection(self.stop_command.format(process))

    def upload_config(self, config_file=None):
        """ 上传supervisor的配置文件
        """
        if not config_file:
            current_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
            config_file = os.path.join(current_path, 'supervisor.conf')
        self.host.put_via_tmp(config_file, self.config_file)

    def install(self):
        """ 安装supervisor
        """
        is_installed, _ = self.host.ssh("apt list | grep supervisor")
        if '[installed]' not in str(is_installed):
            self.host.ssh('apt update', sudo=True)
            self.host.ssh('apt install -y --reinstall supervisor', sudo=True)
            self.upload_config()
        pid = self.host.pid('supervisord')
        if not pid:
            self.host.ssh(f'supervisord -c {self.config_file}', sudo=True)

    def uninstall(self):
        """ 卸载supervisor
        """
        self.host.ssh(f'apt remove supervisor', sudo=True)
