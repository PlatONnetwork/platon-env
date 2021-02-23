import json
from dataclasses import dataclass, field, asdict
from typing import List
from dacite import from_dict
from keytool.key import gen_node_keypair, gen_bls_keypair


@dataclass
class Deploy:
    platon: str
    keystore_dir: str = field(default='')
    deploy_dir: str = field(default='platon')
    local_tmp_dir: str = field(default='tmp')
    install_dependency: bool = field(default=True)
    max_threads: int = field(default=30)


@dataclass
class Chain:
    network: str
    genesis: str = field(default='')
    sync_mode: str = field(default='fast')
    log_level: int = field(default=4)
    debug: bool = field(default=True)
    append_cmd: str = field(default='')


@dataclass
class Config:
    deploy: Deploy
    chain: Chain

    def to_dict(self):
        return asdict(self)


@dataclass
class Base:
    username: str = field(default=None)
    password: str = field(default=None)
    ssh_port: int = field(default=None)
    p2p_port: int = field(default=None)
    rpc_port: int = field(default=None)
    ws_port: int = field(default=None)

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
class Node(Base):
    host: str = field(default=None)
    node_id: str = field(default=None)
    node_key: str = field(default=None)
    bls_pubkey: str = field(default=None)
    bls_prikey: str = field(default=None)

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
class NodeGroup(Base):
    members: List[Node] = field(default=None)

    def __post_init__(self):
        for member in self.members:
            self._fill_common_info(member)


@dataclass
class Nodes(Base):
    init: NodeGroup = field(default=None)
    normal: NodeGroup = field(default=None)

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


if __name__ == "__main__":
    from common.load_file import LoadFile
    config_data = LoadFile('file/config_template.yml').get_data()
    print(f'json = {config_data}')
    config = create_config(config_data)
    print(f'all = {config.to_dict()}')
