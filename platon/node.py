import os
import tarfile
from typing import Union

from loguru import logger
from paramiko.ssh_exception import SSHException

from base.host import Host
from base.process import Process
from utils.path import join_path


class NodeOpts:

    def __init__(self, rpc_port=None, rpc_api=None, ws_port=None, ws_api=None, extra_opts=None):
        self.rpc_port = rpc_port
        self.rpc_api = rpc_api
        self.ws_port = ws_port
        self.ws_api = ws_api
        self.extra_opts = extra_opts

    def __str__(self):
        string = ''
        if self.rpc_port:
            assert self.rpc_api, 'The RPC API is not defined.'
            string += f'--rpc --rpcaddr 0.0.0.0 --rpcport {self.rpc_port} --rpcapi {self.rpc_api} '
        if self.ws_port:
            assert self.ws_api, 'The WS API is not defined.'
            string += f'--ws --wsaddr 0.0.0.0 --wsport {self.rpc_port} --wsapi {self.rpc_api} '
        if self.extra_opts:
            string += self.extra_opts
        return string

    def to_string(self):
        return str(self)


class Node(Process):

    def __init__(self,
                 host: Host,
                 node_id: str,
                 node_key: str,
                 network: str,
                 p2p_port: int = 16789,
                 bls_pubkey: str = None,
                 bls_prikey: str = None,
                 is_init_node: bool = False,
                 base_dir: str = None,
                 ):
        super().__init__(host, base_dir=base_dir, port=p2p_port)
        self.node_id = node_id
        self.node_key = node_key
        self.network = network
        self.p2p_port = p2p_port
        self.bls_pubkey = bls_pubkey
        self.bls_prikey = bls_prikey
        self.is_init_node = is_init_node
        # 连接信息
        self.static_nodes = None
        # 部署信息
        self.name = f'p{self.p2p_port}'
        if not self.base_dir:
            # todo: 是否需要绝对路径？
            self.base_dir = self.name
        self.deploy_path = join_path(self.base_dir, self.name)
        self.platon = join_path(self.deploy_path, 'platon')
        self.data_dir = join_path(self.deploy_path, 'data')
        self.keystore_dir = join_path(self.data_dir, 'keystore')
        self.genesis_file = join_path(self.deploy_path, 'genesis.json')
        self.static_file = join_path(self.deploy_path, 'static-nodes.json')
        self.node_key_file = join_path(self.deploy_path, 'nodekey')
        self.bls_prikey_file = join_path(self.deploy_path, 'blskey')
        self.log_dir = join_path(self.deploy_path, 'log')
        self.log_file = join_path(self.log_dir, 'platon.log')
        self.options = ''
        self.supervisor_file = join_path(self.host.supervisor.process_config_path, self.name + '.conf')

    def __str__(self):
        return f'{self.host.ip}:{self.p2p_port}'

    def __eq__(self, other):
        if self.host == other.host and self.p2p_port == other.p2p_port:
            return True
        return False

    def __hash__(self):
        return hash(id(self))

    @property
    def enode(self):
        """ 获取节点的enode信息
        """
        return f'enode://{self.node_id}@{self.host.ip}:{self.p2p_port}'

    def install(self,
                platon: str,
                network: str,
                genesis_file: str = None,
                static_nodes: str = None,
                keystore_dir: str = None,
                options: str = None,
                ):
        """ 使用supervisor部署节点
        """
        if not self.host.supervisor:
            raise Exception("supervisor not install.")
        self.uninstall()

        # 准备部署所需的文件
        self.upload_platon(platon)

        self.host.write_file(self.node_key, self.node_key_file)

        if self.network == 'private':
            assert genesis_file or self.genesis, 'Private network needs genesis file.'
            self.host.fast_put(genesis_file, self.genesis_file)

        if self.bls_prikey:
            self.host.write_file(self.bls_prikey, self.bls_prikey_file)

        if static_nodes:
            self.set_static_nodes(static_nodes)

        if keystore_dir:
            self.upload_keystore(keystore_dir)

        # 启动节点
        self.init()
        self.start(options)

    def uninstall(self):
        """ 清理节点，会停止节点并删除节点文件
        """
        self.stop()
        self.host.ssh(f'rm -rf {self.deploy_path}')
        self.host.supervisor.remove(self.name)

    def status(self) -> bool:
        """ 获取节点的运行状态
        """
        return self.host.supervisor.status(self.name)

    def init(self):
        """ 初始化节点
        """
        self.host.ssh(f'mkdir {self.log_dir}')
        _, errs = self.host.ssh(f'{self.platon} --datadir {self.data_dir} init {self.genesis_file} > {self.log_dir} 2>&1')
        if errs and ('Fatal' in errs or 'Error' in errs):
            raise SSHException(errs)
        logger.info(f'Node {self} init success!')

    def start(self, options: Union[str, NodeOpts] = ''):
        """ 使用supervisor启动节点
        """
        self.options = str(options)
        self.host.supervisor.add(self.name, self.supervisor_config)
        self.host.supervisor.start(self.name)

    def restart(self):
        """ 使用supervisor重启节点
        """
        self.host.supervisor.restart(self.name)

    def stop(self):
        """ 使用supervisor停止节点
        """
        self.host.supervisor.stop(self.name)

    def upload_platon(self, platon_file):
        """ 使用缓存上传platon
        """
        self.host.fast_put(platon_file, self.platon)
        self.host.ssh(f'chmod u+x {self.platon}')

    def upload_keystore(self, keystore: str):
        """ 使用缓存上传keystore，支持单个文件与目录
        """
        if os.path.isfile(keystore):
            self.host.fast_put(keystore, self.keystore_dir)
        elif os.path.isdir(keystore):
            tar_file = keystore + '.tar.gz'
            tar = tarfile.open(tar_file, "w:gz")
            tar.add(keystore, arcname=os.path.basename(keystore))
            tar.close()
            tmp_file_path = self.host.fast_put(tar_file)
            self.host.ssh(f'tar xzvf {tmp_file_path} {self.keystore_dir}')
        else:
            raise FileNotFoundError('keystore not found.')

    def set_static_nodes(self, enodes: [str]):
        """ 指定要连接的静态节点，可以指定多个
        """
        for enode in enodes:
            assert enode.startswith('enode'), 'enode format is incorrect.'
        self.static_nodes = enodes
        self.host.write_file(self.static_nodes, self.static_file)

    @property
    def supervisor_config(self):
        """ 在远程主机生成节点的supervisor配置文件
        """
        program = f'[program:{self.name}]\n'
        bls_key_cmd = f'--cbft.blskey {self.bls_prikey_file} ' if self.bls_prikey else ''
        command = (f'command={self.platon} --identity {self.name} '
                   f'--datadir {self.data_dir} '
                   f'--port {self.p2p_port} '
                   f'--nodekey {self.node_key_file} '
                   f'{bls_key_cmd}'
                   f'{self.options} \n')
        setting = '\n'.join(['numprocs=1', 'autostart=false', 'startsecs=1', 'startretries=3', 'autorestart=unexpected',
                             'exitcode=0', 'stopsignal=TERM', 'stopwaitsecs=10', 'redirect_stderr=true',
                             'stdout_logfile_maxbytes=200MB', 'stdout_logfile_backups=20',
                             f'stdout_logfile={self.log_file}'])
        config = program + command + setting
        return config
