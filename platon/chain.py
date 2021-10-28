from abc import ABC

from base.host import Host
from base.service import Service
from node import Node
from utils.executor import concurrent_executor


class Chain(Service):
    hosts: list[Host]
    init_nodes: set[Node]
    normal_nodes: set[Node]

    def __init__(self, nodes: [Node] = None):
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

    def install(self, platon, network, genesis_file=None, keystore_dir=None):
        """ 部署链
        """
        nodes = self.nodes
        return concurrent_executor(nodes, 'install', platon, network, genesis_file, keystore_dir)

    def uninstall(self, nodes: list[Node] = None):
        """ 清理链，会停止节点并删除节点文件
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'uninstall')

    def add_process(self, node: Node):
        """ 将进程添加到服务，进行统一管理
        """
        if self.processes.get(node.name):
            raise Exception('The node already exists.')

        self.init_nodes.add(node) if node.is_init_node else self.normal_nodes.add(node)

        self.processes[node.name] = node

    def status(self, nodes: list[Node] = None):
        """ 检查链运行状态
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'status')

    def init(self, nodes: list[Node] = None):
        """ 初始化链
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'init')

    def start(self, nodes: list[Node] = None):
        """ 启动链
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'start')

    def restart(self, nodes: list[Node] = None):
        """ 重启链
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'restart')

    def stop(self, nodes: list[Node] = None):
        """ 停止链
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'stop')

    def upload_platon(self, platon_file, nodes: list[Node] = None):
        """ 使用缓存上传platon
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'upload_platon', platon_file)

    def upload_keystore(self, keystore_path, nodes: list[Node] = None):
        """ 使用缓存上传keystore并解压
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'upload_keystore', keystore_path)

    def set_static_nodes(self, enodes: list[str], nodes: list[Node] = None):
        """ 指定要连接的静态节点，可以指定多个
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'set_static_nodes', enodes)

    @classmethod
    def from_chain_file(cls, file):
        """ 通过chain肖像文件, 生成chain对象
        """
        pass

    def to_chain_file(self):
        """ 通过chain对象，生成chain肖像文件
        """
        pass
