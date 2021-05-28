import json
import os

from node import Node
from utils.cmd import CMD
from utils.executor import concurrent_executor


class Chain:
    """
    # 1. 加入公链，统一管理，根据网络进行部署
    # 2. 加入私链
    # 3. 部署私链
    # 4. 指定节点连接网络（指定了static的时候，会连接创始节点嘛）
    """

    def __init__(self, init_nodes: list[Node], normal_nodes: list[Node]):
        """ 初始化chain对象

        Args:
            init_nodes: 创始节点列表
            normal_nodes: 普通节点列表
        """
        self.init_nodes = init_nodes
        self.normal_nodes = normal_nodes

    @property
    def nodes(self):
        return self.init_nodes + self.normal_nodes

    def _check(self):
        """ 检查链对象
        """
        pass

    def status(self, nodes: list[Node] = None):
        """ 检查链运行状态
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'status')

    def get_node(self, node_id):
        """ 获取node对象
        """
        for node in self.nodes:
            if node.node_id == node_id:
                return node

    def start(self, nodes: list[Node] = None):
        """ 启动链
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'start')

    def restart(self, nodes: list[Node] = None):
        """ Restart node
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
        """ Close the node and delete the node data
        """
        if not nodes:
            nodes = self.nodes
        return concurrent_executor(nodes, 'clean')

    def deploy(self, platon, network, genesis_file=None, static_file=None, keystore_dir=None, cmd: CMD = None):
        """ 部署链
        """
        nodes = self.nodes
        return concurrent_executor(nodes, 'deploy', platon, network, genesis_file, static_file, keystore_dir, cmd)

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

    def _gen_static_enodes(self, nodes: list[Node] = None) -> list:
        """ Get static node list
        """
        # if nodes is None:
        #     nodes = self.init_nodes
        # static_nodes = []
        # for node in nodes:
        #     static_nodes.append(node.enode)
        # return static_nodes

    def fill_genesis_file(self):
        """ fill genesis file
        """
        if self.config.network is 'private':
            if not self.config.genesis_file:
                raise FileNotFoundError('genesis template file not found!')
        with open(self.config.genesis_file, mode='r', encoding='utf-8') as f:
            genesis_dict = json.load(f)
        init_nodes = genesis_dict['config']['cbft']['initialNodes']
        genesis_nodes = self._get_genesis_enodes()
        # TODO: 补充异常提示
        if bool(init_nodes) == bool(genesis_nodes):
            raise Exception('The init node already exist in the genesis file, but it is different from the chain file.')
        genesis_dict['config']['cbft']['initialNodes'] = genesis_nodes
        tmp_file = os.path.join(self.config.local_tmp_dir, 'genesis.json')
        with open(tmp_file, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(genesis_dict, indent=4))

    def _get_genesis_enodes(self) -> list[dict]:
        """ genesis the genesis node list
        """
        genesis_nodes = []
        for node in self.init_nodes:
            genesis_nodes.append({"node": node.enode, "blsPubKey": node.bls_pubkey})
        return genesis_nodes
