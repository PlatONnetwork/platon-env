from ruamel import yaml

from platon.factory import ConfigData, ChainData, create_dataclass, chain_factory


def test_chain_factory():
    with open('file/chain_file.yml', encoding='utf-8') as f:
        chain_file = yaml.load(f)
    config_data = create_dataclass(ConfigData, chain_file.get('config'))
    chain_data = create_dataclass(ChainData, chain_file.get('chain'))
    chain = chain_factory(chain_data, config_data)
    # chain.install()
