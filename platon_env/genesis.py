import json
from typing import List

from platon_env.node import Node


class Genesis:

    def __init__(self, file: str = None):
        self.file = file
        with open(file, mode='r', encoding='utf-8') as file:
            self.data = json.load(file)

    @property
    def init_node(self):
        return self.data['config']['cbft']['initialNodes']

    def fill_init_nodes(self, nodes: List[Node] = None, content: List[dict] = None):
        """ 填写初始验证人信息，支持传入node对象列表，或者初始验证人信息
        """
        init_nodes = []
        if nodes:
            for node in nodes:
                init_nodes.append({"node": node.enode, "blsPubKey": node.bls_pubkey})
        elif content:
            init_nodes = content
        self.data['config']['cbft']['initialNodes'] = init_nodes
        return self

    def fill_accounts(self, accounts: dict):
        """ 填写初始账户信息
        """
        self.data['alloc'] = accounts
        return self

    def save_as(self, file):
        """ 保存为本地文件
        """
        with open(file, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(self.data, indent=4))
