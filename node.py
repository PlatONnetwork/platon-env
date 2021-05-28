import os
import tarfile
from loguru import logger
from paramiko.ssh_exception import SSHException

from utils.cmd import CMD
from utils.path import join_path


class Node:
    def __init__(self, host, node_id, node_key, bls_pubkey=None, bls_prikey=None, p2p_port=16789):
        self.host = host
        self.network = None
        self.node_id = node_id
        self.node_key = node_key
        self.bls_pubkey = bls_pubkey
        self.bls_prikey = bls_prikey
        self.p2p_port = p2p_port
        # deploy info
        self.name = f'p{self.p2p_port}'
        self.tag = f'{self.host.ip}:{self.p2p_port}'
        self.deploy_path = join_path(self.host.base_path, self.name)
        self.platon = join_path(self.deploy_path, 'platon')
        self.data_dir = join_path(self.deploy_path, 'data')
        self.keystore_dir = join_path(self.data_dir, 'keystore')
        self.genesis_file = join_path(self.deploy_path, 'genesis.json')
        self.static_file = join_path(self.deploy_path, 'static-nodes.json')
        self.node_key_file = join_path(self.deploy_path, 'nodekey')
        self.bls_prikey_file = join_path(self.deploy_path, 'blskey')
        self.log_dir = join_path(self.deploy_path, 'log')
        self.log_file = join_path(self.log_dir, 'platon.log')
        self.supervisor_file = join_path(self.host.supervisor.conf_path, self.name + '.conf')

    @property
    def enode(self):
        """ 获取节点的enode信息
        """
        return f'enode://{self.node_id}@{self.host.ip}:{self.p2p_port}'

    def status(self) -> bool:
        """ 获取节点的运行状态
        """
        return self.host.supervisor.status(self.name)

    def init(self):
        """ 初始化节点
        """
        self.host.cmd(f'mkdir {self.log_dir}', mode='strict')
        _, errs = self.host.cmd(f'{self.platon} --datadir {self.data_dir} init {self.genesis_file} > {self.log_dir} 2>&1')
        if errs and ('Fatal' in errs or 'Error' in errs):
            raise SSHException(errs)
        logger.info(f'Node {self.tag} init success!')

    def start(self):
        """ 使用supervisor启动节点
        """
        self.host.supervisor.start(self.name)

    def restart(self):
        """ 使用supervisor重启节点
        """
        self.host.supervisor.restart(self.name)

    def stop(self):
        """ 使用supervisor停止节点
        """
        self.host.supervisor.stop(self.name)

    def clean(self):
        """ 清理节点，会停止节点并删除节点文件
        """
        self.stop()
        self.host.cmd(f'rm -rf {self.deploy_path}')
        self.host.supervisor.remove(self.name)

    def deploy(self, platon, network, genesis_file=None, static_file=None, keystore_dir=None, cmd: CMD = None):
        """ 使用supervisor部署节点
        """
        self.host.supervisor.install()
        self.add_supervisor_cfg(cmd)
        self.clean()
        self._prepare_node_files(platon, network, genesis_file, static_file, keystore_dir)
        self.init()
        self.start()

    def update_cmd(self):
        pass

    def upload_platon(self, platon_file):
        """ 使用缓存上传platon
        """
        self.host.put_file(platon_file, self.platon, mode='tmp')
        self.host.cmd(f'chmod u+x {self.platon}')

    def upload_keystore(self, keystore_path):
        """ 使用缓存上传keystore并解压
        """
        tar_file = keystore_path + '.tar.gz'
        tar = tarfile.open(tar_file, "w:gz")
        tar.add(keystore_path, arcname=os.path.basename(keystore_path))
        tar.close()
        tmp_file_path = self.host.put_file(tar_file)
        self.host.cmd(f'tar xzvf {tmp_file_path} {self.keystore_dir}')

    def _prepare_node_files(self, platon, network, genesis_file=None, static_file=None, keystore_dir=None):
        """ 准备节点部署过程中需要的文件
        TODO: node自己填充genesis文件
        TODO: 从节点生成static文件
        """
        self.upload_platon(platon)
        self.network = network
        if network == 'private':
            assert genesis_file, 'Private network needs genesis file!'
            self.host.put_file(genesis_file, self.genesis_file)
        if static_file:
            self.host.put_file(static_file, self.static_file)
        if keystore_dir:
            self.upload_keystore(keystore_dir)
        self.host.save_to_file(self.node_key, self.node_key_file)
        if self.bls_prikey:
            self.host.save_to_file(self.bls_prikey, self.bls_prikey_file)

    def add_supervisor_cfg(self, cmd: CMD = None):
        """ 在远程主机生成节点的supervisor配置文件
        TODO: 细化supervisor设置项
        """
        program = f'[program:{self.name}]\n'
        bls_key_cmd = f'--cbft.blskey {self.bls_prikey_file} ' if self.bls_prikey else ''
        extra_cmd = cmd.to_string() if cmd else ''
        command = (f'command={self.platon} --identity {self.name} '
                   f'--datadir {self.data_dir} '
                   f'--port {self.p2p_port} '
                   f'--nodekey {self.node_key_file} '
                   f'{bls_key_cmd}'
                   f'{extra_cmd} \n')
        setting = '\n'.join(['numprocs=1', 'autostart=false', 'startsecs=1', 'startretries=3', 'autorestart=unexpected',
                             'exitcode=0', 'stopsignal=TERM', 'stopwaitsecs=10', 'redirect_stderr=true',
                             'stdout_logfile_maxbytes=200MB', 'stdout_logfile_backups=20',
                             f'stdout_logfile={self.log_file}'])
        configs = program + command + setting
        self.host.cmd(f"sh -c 'echo \"{configs}\" > {self.supervisorctl_file}'", self.host.password, sudo=True)
        self.host.supervisor.update()
