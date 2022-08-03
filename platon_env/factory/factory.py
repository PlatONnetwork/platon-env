import json
from dataclasses import dataclass, field, asdict
from typing import List
from dacite import from_dict
from ruamel import yaml

from platon_env.base.host import Host
from platon_env.node import Node
from platon_env.utils.key.keytool import gen_node_keypair, gen_bls_keypair


@dataclass
class CommonData:
    host: str = None
    username: str = None
    password: str = None
    ssh_port: int = 22
    p2p_port: int = None
    options: str = None

    def _fill_common_info(self, node):
        info_dict = asdict(self)
        for k, v in info_dict.items():
            if not v:
                continue
            if hasattr(node, k) and not getattr(node, k):
                setattr(node, k, v)

    def to_dict(self):
        return asdict(self)


@dataclass
class NodeData(CommonData):
    node_id: str = None
    node_key: str = None
    bls_pubkey: str = None
    bls_prikey: str = None

    def __post_init__(self):
        self._fill_node_info()

    def _fill_node_info(self):
        if not self.node_id or not self.node_key:
            node_id, node_key = gen_node_keypair()
            self.node_id = node_id
            self.node_key = node_key
        if not self.bls_pubkey or not self.bls_prikey:
            bls_pubkey, bls_prikey = gen_bls_keypair()
            self.bls_pubkey = bls_pubkey
            self.bls_prikey = bls_prikey


@dataclass
class NodeGroupData(CommonData):
    nodes: List[NodeData] = field(default_factory=[])

    def __post_init__(self):
        for node in self.nodes:
            self._fill_common_info(node)


@dataclass
class ChainData:
    platon: str
    network: str
    genesis: str
    keystore: str
    ssl: bool
    static_nodes: List[str] = field(default_factory=[])
    deploy_dir: str = None
    init: NodeGroupData = None
    normal: NodeGroupData = None


def create_dataclass(cls, _dict):
    """ 将dict数据转换为dataclass对象
    """
    return from_dict(cls, _dict)


def save_dataclass(obj, file):
    """ 将dataclass对象存储为文件
    # todo: 实现存储为yaml文件
    """
    data = obj.to_dict()
    with open(file, "w") as f:
        f.write(json.dumps(data, indent=4))


def chain_factory(file: str):
    """ 根据chain配置文件生成chain对象
    # todo: 支持无密码连接
    """
    with open(file, encoding='utf-8') as f:
        data = yaml.load(f, Loader=yaml.Loader)
    chain_data = create_dataclass(ChainData, data['chain'])

    nodes = []
    # todo: 增加host去重
    init_nodes = chain_data.init.nodes if chain_data.init else []
    for member in init_nodes:
        host = Host(member.host,
                    member.username,
                    password=member.password,
                    port=member.ssh_port,
                    is_superviosr=True,
                    )
        node = Node(host,
                    chain_data.platon,
                    chain_data.network,
                    genesis_file=chain_data.genesis,
                    keystore=chain_data.keystore,
                    p2p_port=member.p2p_port,
                    node_id=member.node_id,
                    node_key=member.node_key,
                    bls_pubkey=member.bls_pubkey,
                    bls_prikey=member.bls_prikey,
                    is_init_node=True,
                    options=member.options,
                    ssl=chain_data.ssl,
                    base_dir=chain_data.deploy_dir,
                    )
        nodes.append(node)

    normal_nodes = chain_data.normal.nodes if chain_data.normal else []
    for member in normal_nodes:
        host = Host(member.host,
                    member.username,
                    password=member.password,
                    port=member.ssh_port,
                    is_superviosr=True,
                    )
        node = Node(host,
                    chain_data.platon,
                    chain_data.network,
                    genesis_file=chain_data.genesis,
                    keystore=chain_data.keystore,
                    p2p_port=member.p2p_port,
                    node_id=member.node_id,
                    node_key=member.node_key,
                    bls_pubkey=member.bls_pubkey,
                    bls_prikey=member.bls_prikey,
                    is_init_node=False,
                    options=member.options,
                    ssl=chain_data.ssl,
                    base_dir=chain_data.deploy_dir,
                    )
        nodes.append(node)

    from platon_env.chain import Chain
    return Chain(nodes, genesis_file=chain_data.genesis)
