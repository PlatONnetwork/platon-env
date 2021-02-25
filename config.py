import json
from dataclasses import dataclass, field, asdict
from typing import List
from dacite import from_dict
from keytool.key import gen_node_keypair, gen_bls_keypair


@dataclass
class Config:
    platon: str
    network: str
    genesis_file: str = ''
    keystore_dir: str = ''
    deploy_dir: str = 'platon'
    local_tmp_dir: str = 'tmp'
    remote_tmp_dir: str = 'tmp'
    install_dependency: bool = True
    max_threads: int = 30
    sync_mode: str = 'fast'
    log_level: int = 4
    debug: bool = True
    append_cmd: str = ''
    static_nodes: List[str] = field(default_factory=[])

    def to_dict(self):
        return asdict(self)


@dataclass
class Host:
    host: str = None
    username: str = None
    password: str = None
    ssh_port: int = 22


@dataclass
class CommonInfo(Host):
    p2p_port: int = None
    rpc_port: int = None
    ws_port: int = None

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
class Node(CommonInfo):
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
class NodeGroup(CommonInfo):
    members: List[Node] = field(default_factory=[])

    def __post_init__(self):
        for member in self.members:
            self._fill_common_info(member)


@dataclass
class Nodes(CommonInfo):
    init: NodeGroup = None
    normal: NodeGroup = None

    def __post_init__(self):
        members = self.init.members + self.normal.members
        for member in members:
            self._fill_common_info(member)
        self.__check_nodes()

    def __check_nodes(self):
        # TODO: complete the code
        pass


# create config obj
def create_config(config_dict) -> Config:
    return from_dict(Config, config_dict)


# create nodes obj
def create_nodes(nodes_dict) -> Nodes:
    return from_dict(Nodes, nodes_dict)


def to_file(self, file):
    data = self.to_dict()
    with open(file, "w") as f:
        f.write(json.dumps(data, indent=4))

