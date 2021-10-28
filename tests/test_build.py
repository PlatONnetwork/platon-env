import yaml
from platon.chain import Chain
from platon.data import dict_to_obj, ConfigData, ChainData


def test_base_deploy():
    # load config file
    with open('file/chain_file.yml', encoding='utf-8') as f:
        chain_file = yaml.load(f)
    # generate config
    config = dict_to_obj(ConfigData, chain_file.get('config'))
    # logger.debug(f'ConfigData: {config.to_dict()}')
    # generate nodes
    nodes = dict_to_obj(ChainData, chain_file.get('chain'))
    # logger.debug(f'Nodes: {nodes.to_dict()}')
    # init chain/host/node obj
    # chain = Chain(nodes, config)
    # logger.info(f'chain = {chain.__dict__}')
    # chain.deploy(chain.nodes)


def test_add_to_platon():
    pass


def test_add_to_alaya():
    pass


def test_deploy_private_chain():
    pass


def test_add_to_private_chain():
    pass
