import json
import os


class Genesis:
    template_file = ''

    def fill_init_nodes(self, nodes, template_file=None, to_file=None):
        """ 填写初始验证人信息
        """
        if not template_file:
            template_file = self.template_file
        assert os.path.exists(template_file), 'genesis template file not found!'
        with open(template_file, mode='rw', encoding='utf-8') as file:
            genesis_dict = json.load(file)
        genesis_nodes = []
        for node in nodes:
            genesis_nodes.append({"node": node.enode, "blsPubKey": node.bls_pubkey})
        genesis_dict['config']['cbft']['initialNodes'] = genesis_nodes
        if not to_file:
            to_file = template_file
        with open(to_file, mode='w', encoding='utf-8') as file:
            file.write(json.dumps(genesis_dict, indent=4))

    def fill_accounts(self, accounts):
        """ 填写初始账户信息
        """
        pass




