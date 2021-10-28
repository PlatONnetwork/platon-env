import json
from dataclasses import dataclass, field, asdict
from typing import List
from dacite import from_dict
from utils.key.keytool import gen_node_keypair, gen_bls_keypair


@dataclass
class ConfigData:
    platon: str
    network: str
    genesis_file: str = ''
    keystore_dir: str = ''
    deploy_dir: str = ''
    local_tmp_dir: str = 'tmp'
    remote_tmp_dir: str = 'tmp'
    install_dependency: bool = True
    max_threads: int = 30
    sync_mode: str = 'fast'
    log_level: int = 4
    append_cmd: str = ''
    static_nodes: List[str] = field(default_factory=[])

    def to_dict(self):
        return asdict(self)


@dataclass
class CommonData:
    host: str = None
    username: str = None
    password: str = None
    ssh_port: int = 22
    p2p_port: int = None
    rpc_port: int = None
    ws_port: int = None

    def _fill_member_info(self, node):
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
    members: List[NodeData] = field(default_factory=[])

    def __post_init__(self):
        for member in self.members:
            self._fill_member_info(member)


@dataclass
class ChainData(CommonData):
    init: NodeGroupData = None
    normal: NodeGroupData = None

    def __post_init__(self):
        members = self.init.members + self.normal.members
        for member in members:
            self._fill_member_info(member)
        self.__check_nodes()

    def __check_nodes(self):
        """ 检查节点信息是否完善与正确
        """
        # todo: 完成编码
        pass


# create obj from dict
def dict_to_obj(cls, obj_dict):
    return from_dict(cls, obj_dict)


# save obj to file
def obj_to_file(obj, file):
    data = obj.to_dict()
    with open(file, "w") as f:
        f.write(json.dumps(data, indent=4))
