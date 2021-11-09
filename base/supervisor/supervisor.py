import os

from base.process import Process
from utils.path import join_path


class Supervisor(Process):
    base_path = '/etc/supervisor'
    config_file = '/etc/supervisor/supervisord.conf'
    process_config_path = '/etc/supervisor/conf.d'
    status_command = 'supervisorctl status {}'
    start_command = 'supervisorctl start {}'
    restart_command = 'supervisorctl restart {}'
    stop_command = 'supervisorctl stop {}'
    update_command = 'supervisorctl update'

    def __init__(self, host):
        super().__init__(host)
        # host.set_supervisor(self)

    def install(self):
        """ 安装supervisor
        todo: 有些文件需要创建
            sudo touch /var/run/supervisor.sock
            sudo chmod 777 /var/run/supervisor.sock
            sudo supervisord -c /etc/supervisor/supervisord.conf
        """
        is_installed = self.host.ssh("apt list | grep supervisor")
        if '[installed]' not in str(is_installed):
            self.host.ssh('apt update', sudo=True)
            self.host.ssh('apt install -y --reinstall supervisor', sudo=True)
            # self.host.ssh('apt update')
            # self.host.ssh('apt install -y --reinstall supervisor')
            self._upload_config()
        pid = self.host.pid('supervisord')

        if not pid:
            print("not pid")
            # self.host.ssh('touch /var/run/supervisor.sock', sudo=True)

            # self.host.ssh('service supervisor restart', sudo=True)
            self.host.ssh(f'supervisord -c {self.config_file}', sudo=True)
            # self.host.ssh('supervisord -c /etc/supervisor/supervisord.conf', sudo=True)
        # self.host.ssh('touch /var/run/supervisor.sock', sudo=True)
        # self.host.ssh('chmod 777 /var/run/supervisor.sock', sudo=True)
        # self.host.ssh('sudo service supervisor restart', sudo=True)
        self.host.ssh('chmod 770 /var/run/supervisor.sock', sudo=True)
        print('111')

    def uninstall(self):
        """ 卸载supervisor
        """
        self.host.ssh(f'apt remove supervisor', sudo=True)

    def add(self, name, config=None, file=None):
        """ 为supervisor添加要管理的进程，支持name + config的方式，或者直接上传配置文件以添加进程。
        """
        config_path = join_path(self.process_config_path, f'{name}.conf')

        if config:
            self.host.ssh(f"sh -c 'echo \"{config}\" > {config_path}'", sudo=True)
        elif file:
            self.host.fast_put(file, config_path)
        else:
            raise ValueError('All parameters are not available.')
        self.update()

    def remove(self, name):
        """ 通过进程名称，删除supervisor管理的进程
        """
        process_file = os.path.join(self.process_config_path + '/', str(name) + '.conf')
        self.host.ssh(f'rm -rf {process_file}', sudo=True)
        self.update()

    def status(self, name='') -> bool:
        """ 通过进程名称，查看进程状态
        """
        outs = self.host.ssh(self.status_command.format(name))
        if not outs or 'RUNNING' in str(outs):
            return True
        return False

    def update(self):
        """ 更新supervisor的进程列表
        """
        # self.host.connection(self.update_command)
        self.host.ssh(self.update_command)

    def start(self, name):
        """ 启动进程
        """
        # self.host.ssh(self.start_command.format(name))
        self.host.ssh(self.start_command.format(name), sudo=True)

    def restart(self, name):
        """ 重启进程
        """
        self.host.ssh(self.restart_command.format(name))

    def stop(self, name):
        """ 停止进程
        """
        self.host.ssh(self.stop_command.format(name))

    def _upload_config(self, file=None):
        """ 上传supervisor的配置文件
        """
        if not file:
            current_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
            file = os.path.join(current_path, 'supervisor.conf')
        self.host.fast_put(file, self.config_file)
