import os
import tarfile
from loguru import logger
from paramiko.ssh_exception import SSHException

from base.service import Service
from utils.path import join_path


class Node(Service):
    def __init__(self, host, node_id, node_key, bls_pubkey=None, bls_prikey=None, p2p_port=16789):
        self.host = host
        self.node_id = node_id
        self.node_key = node_key
        self.bls_pubkey = bls_pubkey
        self.bls_prikey = bls_prikey
        self.p2p_port = p2p_port
        # 连接信息
        self.network = None
        self.static_nodes = None
        # 部署信息
        self.name = f'p{self.p2p_port}'
        self.tag = f'{self.host.ip}:{self.p2p_port}'
        self.start_options = ''
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
        self.supervisor_file = join_path(self.host.supervisor.process_config_path, self.name + '.conf')

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

    def set_static_nodes(self, enodes):
        """ 指定要连接的静态节点，可以指定多个
        """
        self.static_nodes = enodes
        self.host.save_to_file(self.static_nodes, self.static_file)

    def set_start_options(self, start_options):
        """ 指定节点的启动参数
        """
        self.start_options = start_options
        self.host.supervisor.add_via_node(self)

    def _prepare_files(self, platon, network, genesis_file=None, keystore_dir=None):
        """ 准备节点部署过程中需要的文件
        """
        self.upload_platon(platon)
        self.host.save_to_file(self.node_key, self.node_key_file)
        if self.bls_prikey:
            self.host.save_to_file(self.bls_prikey, self.bls_prikey_file)
        if self.static_nodes:
            self.host.save_to_file(self.static_nodes, self.static_file)
        self.network = network
        if self.network == 'private':
            assert genesis_file, 'Private network needs genesis file!'
            self.host.put_file(genesis_file, self.genesis_file)
        if keystore_dir:
            self.upload_keystore(keystore_dir)

    def deploy(self, platon, network, genesis_file=None, keystore_dir=None):
        """ 使用supervisor部署节点
        """
        self.host.supervisor.install()
        self.host.supervisor.add_via_node(self)
        self.clean()
        self._prepare_files(platon, network, genesis_file, keystore_dir)
        self.init()
        self.start()