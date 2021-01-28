import os
import sys
from client_sdk_python.packages.platon_keys import keys
from client_sdk_python.packages.eth_utils.curried import (
    keccak,
    text_if_str,
    to_bytes
)

def gen_node_keypair():
    extra_entropy = ''
    extra_key_bytes = text_if_str(to_bytes, extra_entropy)
    key_bytes = keccak(os.urandom(32) + extra_key_bytes)
    private_key = keys.PrivateKey(key_bytes)
    return private_key.to_hex()[2:], keys.private_key_to_public_key(private_key).to_hex()[2:]


def gen_bls_keypair():
    if 'linux' in sys.platform:
        tool_file = os.path.abspath('bin/keytool')
        execute_cmd('chmod +x {}'.format(tool_file))
    elif 'win' in sys.platform:
        tool_file = os.path.abspath('bin/keytool.exe')
    else:
        raise Exception('This platform is not supported currently')
    keypair = execute_cmd(f'{tool_file} genblskeypair')
    if not keypair:
        raise Exception('Unable generate bls keypair')
    lines = keypair.split('\n')
    private_key = lines[0].split(':')[1].strip()
    public_key = lines[1].split(':')[1].strip()
    if not private_key or not public_key:
        raise Exception('Incorrect  bls keypair')
    return private_key, public_key


def execute_cmd(cmd):
    r = os.popen(cmd)
    out = r.read()
    r.close()
    return out


if __name__ == '__main__':
    print(gen_node_keypair())
    print(gen_bls_keypair())
