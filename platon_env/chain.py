from typing import Union, List, Set

from platon_env.base.host import Host
from platon_env.base.service import Service
from platon_env.node import Node, NodeOpts
from platon_env.factory import chain_factory
from platon_env.genesis import Genesis
from platon_env.utils.executor import concurrent_executor


class Chain(Service):
    # todo: 对基本参数异常、并发异常进行测试
    hosts: Set[Host] = set()
    init_nodes: Set[Node] = set()
    normal_nodes: Set[Node] = set()

    def __init__(self, nodes: List[Node] = None):
        """ 初始化chain对象
        """
        super().__init__()
        if not nodes:
            nodes = []
        for node in nodes:
            self.add_process(node)

    @property
    def nodes(self):
        return set.union(self.init_nodes, self.normal_nodes)

    def install(self,
                platon: str,
                network: str,
                genesis_file: str = None,
                static_nodes: List[str] = None,
                keystore: str = None,
                options: str = '',
                nodes: List[Node] = None,
                ):
        """ 部署链
        """
        nodes = nodes or self.nodes
        if network == 'private' and genesis_file:
            self.full_genesis_file(genesis_file, nodes)
            static_nodes = static_nodes or [node.enode for node in nodes]

        return concurrent_executor(nodes,
                                   'install',
                                   platon,
                                   network,
                                   genesis_file,
                                   static_nodes,
                                   keystore,
                                   options,
                                   )

    def uninstall(self, nodes: List[Node] = None):
        """ 清理链，会停止节点并删除节点文件
        """
        nodes = nodes or self.nodes
        return concurrent_executor(nodes, 'uninstall')

    def add_process(self, node: Node):
        """ 将进程添加到服务，进行统一管理
        """
        if self.processes.get(id(node)):
            raise Exception('The node already exists.')

        self.init_nodes.add(node) if node.is_init_node else self.normal_nodes.add(node)
        self.hosts.add(node.host)

        self.processes[id(node)] = node

    def status(self, nodes: List[Node] = None):
        """ 检查链运行状态
        """
        nodes = nodes or self.nodes
        return concurrent_executor(nodes, 'status')

    def init(self, nodes: List[Node] = None):
        """ 初始化链
        """
        nodes = nodes or self.nodes
        return concurrent_executor(nodes, 'init')

    def start(self,
              options: Union[str, NodeOpts] = '',
              nodes: List[Node] = None,
              ):
        """ 启动链
        """
        nodes = nodes or self.nodes
        return concurrent_executor(nodes, 'start', options)

    def restart(self, nodes: List[Node] = None):
        """ 重启链
        """
        nodes = nodes or self.nodes
        return concurrent_executor(nodes, 'restart')

    def stop(self, nodes: List[Node] = None):
        """ 停止链
        """
        nodes = nodes or self.nodes
        return concurrent_executor(nodes, 'stop')

    def upload_platon(self, platon_file, nodes: List[Node] = None):
        """ 使用缓存上传platon
        """
        nodes = nodes or self.nodes
        return concurrent_executor(nodes, 'upload_platon', platon_file)

    def upload_keystore(self, keystore_path, nodes: List[Node] = None):
        """ 使用缓存上传keystore并解压
        """
        nodes = nodes or self.nodes
        return concurrent_executor(nodes, 'upload_keystore', keystore_path)

    def set_static_nodes(self, enodes: List[str], nodes: List[Node] = None):
        """ 指定要连接的静态节点，可以指定多个
        """
        nodes = nodes or self.nodes
        return concurrent_executor(nodes, 'set_static_nodes', enodes)

    def full_genesis_file(self, genesis_file, nodes: List[Node] = None):
        nodes = nodes or self.nodes
        init_node = [node for node in nodes if node.is_init_node]
        genesis = Genesis(genesis_file)
        if init_node:
            genesis.fill_init_nodes(init_node)

        if not genesis.init_node:
            raise ValueError('the genesis file init node is empty, and no init node in the nodes argument.')

        genesis.save(genesis_file)

    @staticmethod
    def from_file(file):
        """ 通过chain肖像文件, 生成chain对象
        """
        return chain_factory(file)

    def to_file(self):
        """ 通过chain对象，生成chain肖像文件
        """
        # todo: 待完成编码
        pass
