import os
from platon_env.chain import Chain
from utils.path import join_path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

chain_file = join_path(BASE_DIR, 'file/chain_file.yml')

chain = Chain.from_file(chain_file)
chain.install()
#
# def test_chain_factory():
#     chain = Chain.from_file(chain_file)
#     chain.install(platon, 'private', genesis_file)
