import os
from utils.path import join_path

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

chain_file = join_path(TEST_DIR, 'file/chain_file_local.yml')
genesis_file = join_path(TEST_DIR, 'file/genesis.json')
platon = join_path(TEST_DIR, 'file/platon')
