import os
import yaml
from chain import Chain
from config import create_config, create_nodes
from loguru import logger


def test_base_deploy():
    # load config file
    with open('file/chain_file.yml', encoding='utf-8') as f:
        chain_file = yaml.load(f)
    # generate config
    config = create_config(chain_file.get('config'))
    # logger.debug(f'Config: {config.to_dict()}')
    # generate nodes
    nodes = create_nodes(chain_file.get('nodes'))
    # logger.debug(f'Nodes: {nodes.to_dict()}')
    # init chain/host/node obj
    chain = Chain(nodes, config)
    # logger.info(f'chain = {chain.__dict__}')
    chain.deploy(chain.nodes)


def test_add_to_platon():
    pass


def test_add_to_alaya():
    pass


def test_deploy_private_chain():
    pass


def test_add_to_private_chain():
    pass
