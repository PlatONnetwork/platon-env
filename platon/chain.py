from platon.node import Node
from utils.executor import concurrent_executor


class Chain:

    def __init__(self, init_nodes: list[Node], normal_nodes: list[Node]):
        """ 初始化chain对象

        Args:
            init_nodes: 创始节点列表
            normal_nodes: 普通节点列表
        """
        self.init_nodes = init_nodes
        self.normal_nodes = normal_nodes
        self.static_nodes = None
        self.start_command = ''

    @property
    def nodes(self):
        return self.init_nodes + self.normal_nodes

    def get_node(self, node_id):
        """ 获取node对象
        """
        for node in self.nodes:
            if node.node_id == node_id:
                return node

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

    def clean(self, nodes: list[Node] = None):
        """ 清理链，会停止节点并删除节点文件
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'clean')

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

    def set_static_nodes(self, enodes, nodes: list[Node] = None):
        """ 指定要连接的静态节点，可以指定多个
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'set_static_nodes', enodes)

    def set_start_options(self, start_options, nodes: list[Node] = None):
        """ 指定节点的启动参数
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'set_start_options', start_options)

    def deploy(self, platon, network, genesis_file=None, keystore_dir=None):
        """ 部署链
        """
        nodes = self.nodes
        return concurrent_executor(nodes, 'deploy', platon, network, genesis_file, keystore_dir)

    def install_supervisor(self, nodes: list[Node] = None):
        """ 安装supervisor
        """
        if not nodes:
            nodes = self.nodes

        supervisors = set(node.host.supervisor for node in nodes)
        return concurrent_executor(supervisors, 'install')

    def uninstall_supervisor(self, nodes: list[Node] = None):
        """ 卸载supervisor
        """
        if not nodes:
            nodes = self.nodes

        supervisors = set(node.host.supervisor for node in nodes)
        return concurrent_executor(supervisors, 'uninstall')
