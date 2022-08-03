import os

from loguru import logger

from platon_env.base.process import Process
from platon_env.utils import join_path


class Supervisor(Process):
    base_path = '/etc/supervisor'
    config_file = '/etc/supervisor/supervisord.conf'
    process_config_path = '/etc/supervisor/conf.d'
    status_command = 'supervisorctl status {}'
    start_command = 'supervisorctl start {}'
    restart_command = 'supervisorctl restart {}'
    stop_command = 'supervisorctl stop {}'
    update_command = 'supervisorctl update {}'

    def install(self):
        """ 安装supervisor
        """
        is_installed = self.host.ssh("apt list | grep supervisor", warn=False)
        if '[installed]' not in str(is_installed):
            self.host.ssh('apt update', sudo=True, warn=False)
            self.host.ssh('apt install -y --reinstall supervisor', sudo=True, warn=False)
            self._upload_config()
            logger.info(f'Supervisor install success!')

        pid = self.host.pid('supervisord')
        if not pid:
            # todo: 增加 config_file 不存在的判断
            self.host.ssh(f'supervisord -c {self.config_file}', sudo=True, warn=False)
            self.host.ssh('chmod 770 /var/run/supervisor.sock', sudo=True)

    def uninstall(self):
        """ 卸载supervisor
        """
        self.host.ssh(f'apt remove supervisor', sudo=True, warn=False)
        logger.info(f'Supervisor {self.host.ip} uninstall success!')

    def add(self, name, config=None, file=None):
        """ 为supervisor添加要管理的进程，支持name + config的方式，或者直接上传配置文件以添加进程。
        """
        config_path = join_path(self.process_config_path, f'{name}.conf')

        if config:
            self.host.ssh(f"sh -c 'echo \"{config}\" > {config_path}'", sudo=True, warn=False)
        elif file:
            self.host.fast_put(file, config_path)
        else:
            raise ValueError('All parameters are not available.')
        self.update(name)

    def remove(self, name):
        """ 通过进程名称，删除supervisor管理的进程
        """
        process_file = join_path(self.process_config_path, f'{name}.conf')
        self.host.ssh(f'rm -rf {process_file}', sudo=True, warn=False)
        self.update(name)

    def status(self, name='') -> bool:
        """ 通过进程名称，查看进程状态
        """
        outs = self.host.ssh(self.status_command.format(name))
        if not outs or 'RUNNING' in str(outs):
            return True
        return False

    def update(self, name=''):
        """ 更新supervisor的进程列表
        """
        self.host.ssh(self.update_command.format(name), warn=False)

    def start(self, name):
        """ 启动进程
        """
        self.host.ssh(self.start_command.format(name), warn=False)

    def restart(self, name):
        """ 重启进程
        """
        self.host.ssh(self.restart_command.format(name), warn=False)

    def stop(self, name):
        """ 停止进程
        """
        self.host.ssh(self.stop_command.format(name), warn=False)

    def _upload_config(self, file=None):
        """ 上传supervisor的配置文件
        """
        if not file:
            current_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
            file = join_path(current_path, 'supervisor.conf')
        self.host.fast_put(file, self.config_file, sudo=True)
