import yaml

from chain import Chain
from config import create_config, create_nodes

from loguru import logger


def test_deploy():
    # load config file
    file = 'file/config_template.yml'
    with open(file, encoding='utf-8') as f:
        data = yaml.load(f)
    # generate config and nodes obj
    config_dict = data.get('config')
    config = create_config(config_dict)
    logger.info(f'config = {config.to_dict()}')
    nodes_dict = data.get('nodes')
    nodes = create_nodes(nodes_dict)
    logger.info(f'nodes = {nodes.to_dict()}')
    # init chain/host/node obj
    chain = Chain(nodes, config)
    logger.info(f'chain = {chain.__dict__}')