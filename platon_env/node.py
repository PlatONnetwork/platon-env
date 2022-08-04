import os
import re
from typing import List, Literal

from loguru import logger
from paramiko.ssh_exception import SSHException
from platon_aide import Aide

from platon_env.base.host import Host
from platon_env.base.process import Process
from platon_env.utils import join_path, do_once
from platon_env.utils import tar_files


class Node(Process):

    def __init__(self,
                 host: Host,
                 platon: str,
                 network: str,
                 genesis_file: str = None,
                 keystore: str = None,
                 p2p_port: int = 16789,
                 node_id: str = None,
                 node_key: str = None,
                 bls_pubkey: str = None,
                 bls_prikey: str = None,
                 static_nodes: List[str] = None,
                 is_init_node: bool = False,
                 options: str = '',
                 ssl: bool = False,
                 base_dir: str = 'platon',
                 ):
        super().__init__(host, port=p2p_port, name=f'p{p2p_port}', base_dir=base_dir)
        # 本地文件信息
        self.loc_platon = platon
        self.loc_genesis = genesis_file
        self.loc_keystore = keystore
        # 节点信息
        self.network = network
        self.node_id = node_id
        self.node_key = node_key
        self.bls_pubkey = bls_pubkey
        self.bls_prikey = bls_prikey
        self.p2p_port = p2p_port
        self.options = options
        self.static_nodes = static_nodes
        self.is_init_node = is_init_node
        # 远程部署信息
        self.deploy_path = join_path(self.base_dir, self.name)
        self.platon = join_path(self.deploy_path, 'platon')
        self.genesis_file = join_path(self.deploy_path, 'genesis.json')
        self.node_key_file = join_path(self.deploy_path, 'nodekey')
        self.bls_prikey_file = join_path(self.deploy_path, 'blskey')
        self.data_dir = join_path(self.deploy_path, 'data')
        self.static_file = join_path(self.data_dir, 'static-nodes.json')
        self.keystore_dir = join_path(self.data_dir, 'keystore')
        self.log_dir = join_path(self.deploy_path, 'log')
        self.log_file = join_path(self.log_dir, 'platon.log')
        self.supervisor_file = join_path(self.host.supervisor.process_config_path, self.name + '.conf')
        # 接口信息
        self.ssl = ssl
        self.current_aide: Aide = None

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
        return f"enode://{self.node_id}@{self.host.ip}:{self.p2p_port}"

    def gql(self, scheme: Literal['ws', 'http'] = None):
        """ 获取节点的graphql连接信息
        注意：当前仅支持http方式，其他scheme为超前设计
        """
        match = re.search('--graphql', self.options)

        if match:
            return f"{self.rpc(scheme)}/graphql/platon"

        return None

    def rpc(self, scheme: Literal['ws', 'http'] = None):
        """ 获取节点的rpc连接信息
        """
        options = self.options + ' '  # 在后面添加' '，避免出现miss match
        ws_match = re.search('--wsport (.+?) ', options)
        http_match = re.search('--rpcport (.+?) ', options)

        if (scheme == 'ws' or not scheme) and ws_match:
            if self.ssl:
                scheme = 'wss'
            return f"{scheme}://{self.host.ip}:{ws_match.group(1)}"

        if (scheme == 'http' or not scheme) and http_match:
            if self.ssl:
                scheme = 'https'
            return f"{scheme}://{self.host.ip}:{http_match.group(1)}"

        raise ValueError(f'The rpc is not open.')

    @property
    def ipc(self):
        """ 获取节点的rpc连接信息
        """
        options = self.options + ' '  # 在后面添加' '，避免出现mis
        ipc_match = re.search('--ipcpath (._?) ', options)

        if ipc_match:
            return ipc_match.group(1)

        raise ValueError(f'The ipc is not open.')

    @property
    def aide(self):
        if not self.current_aide:
            self.current_aide = Aide(self.rpc(), self.gql())

        return self.current_aide

    def install(self,
                platon: str = None,
                network: str = None,
                genesis_file: str = None,
                keystore: str = None,
                static_nodes: List[str] = None,
                options: str = '',
                ):
        """ 使用supervisor部署节点
        """
        if not self.host.supervisor:
            raise Exception("supervisor not install.")
        # 可指定参数
        platon = platon or self.loc_platon
        genesis_file = genesis_file or self.loc_genesis
        keystore = keystore or self.loc_keystore
        network = network or self.network
        static_nodes = static_nodes or self.static_nodes
        options = options or self.options
        # 准备部署所需的文件
        self.uninstall()
        self.upload_platon(platon)
        # todo: 判断节点一定存在节点私钥, 没有则生成
        self.host.write_file(self.node_key, self.node_key_file)
        # todo: 判断初始节点一定存在bls私钥, 没有则生成
        if self.bls_prikey:
            self.host.write_file(self.bls_prikey, self.bls_prikey_file)

        if network == 'private':
            if not genesis_file:
                raise ValueError('Private network needs genesis file.')
            self.host.connection.put(genesis_file, self.genesis_file)
        if keystore:
            self.upload_keystore(keystore)
        if static_nodes:
            self.set_static_nodes(static_nodes)

        # 重置接口信息
        self.current_aide = None
        # 启动节点
        self.init()
        self.start(options)

        logger.info(f'Node {self} install success!')

    def uninstall(self):
        """ 清理节点，会停止节点并删除节点文件
        """
        self.stop()
        self.host.ssh(f'rm -rf {self.deploy_path}', sudo=True)
        self.host.supervisor.remove(self.name)
        logger.info(f'Node {self} uninstall success!')

    def status(self) -> bool:
        """ 获取节点的运行状态
        """
        return self.host.supervisor.status(self.name)

    def init(self):
        """ 初始化节点
        """
        self.host.ssh(f'mkdir -p {self.log_dir}')
        result = self.host.ssh(f'{self.platon} --datadir {self.data_dir} init {self.genesis_file}',
                               warn=False, strip=False)
        if result.failed or ('Fatal' in result.stderr or 'Error' in result.stderr):
            raise SSHException(result.stderr)
        logger.info(f'Node {self} init success!')

    def start(self, options: str = ''):
        """ 使用supervisor启动节点
        """
        self.options = options or self.options
        self.host.supervisor.add(self.name, self.supervisor_config)
        self.host.supervisor.start(self.name)
        logger.info(f'Node {self} start success!')

    def restart(self):
        """ 使用supervisor重启节点
        """
        self.host.supervisor.restart(self.name)
        logger.info(f'Node {self} restart success!')

    def stop(self):
        """ 使用supervisor停止节点
        """
        self.host.supervisor.stop(self.name)
        logger.info(f'Node {self} stop success!')

    def upload_platon(self, platon_file):
        """ 使用缓存上传platon
        """
        self.host.fast_put(platon_file, self.platon)
        self.host.ssh(f'chmod u+x {self.platon}')
        logger.debug(f'Node {self} upload platon success!')

    def upload_keystore(self, keystore: str):
        """ 使用缓存上传keystore，支持单个文件与目录
        """
        if os.path.isfile(keystore):
            self.host.fast_put(keystore, self.keystore_dir)
        elif os.path.isdir(keystore):
            tar_file = keystore + '.tar.gz'
            do_once(tar_files, source=keystore, dest=tar_file)
            tmp_file_path = self.host.fast_put(tar_file)
            self.host.ssh(f'mkdir -p {self.data_dir}')
            self.host.ssh(f'tar xzvf {tmp_file_path} -C {self.data_dir}')
        else:
            raise FileNotFoundError('keystore not found.')
        logger.debug(f'Node {self} upload keystore success!')

    def set_static_nodes(self, enodes: List[str]):
        """ 指定要连接的静态节点，可以指定多个
        """
        for enode in enodes:
            assert 'enode://' in enode, 'enode format is incorrect.'
        self.static_nodes = enodes

        formatted_enodes = str(enodes).replace("'", '"')
        self.host.write_file(formatted_enodes, self.static_file)
        logger.debug(f'Node {self} set static nodes success!')

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
