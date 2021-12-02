import os
import sys

from platon_keys import keys
from platon_utils.curried import keccak, text_if_str, to_bytes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def gen_node_keypair(extra_entropy=''):
    extra_key_bytes = text_if_str(to_bytes, extra_entropy)
    key_bytes = keccak(os.urandom(32) + extra_key_bytes)
    private_key = keys.PrivateKey(key_bytes)
    return keys.private_key_to_public_key(private_key).to_hex()[2:], private_key.to_hex()[2:],


def gen_bls_keypair():
    if 'linux' in sys.platform:
        tool_file = os.path.abspath(os.path.join(BASE_DIR, 'bin/keytool'))
        execute_cmd('chmod +x {}'.format(tool_file))
    elif 'win' in sys.platform:
        tool_file = os.path.abspath(os.path.join(BASE_DIR, 'bin/keytool.exe'))
    else:
        raise Exception('This platform is not supported currently')
    keypair = execute_cmd(f'{tool_file} genblskeypair')
    if not keypair:
        raise Exception('Unable generate bls keypair')
    lines = keypair.split('\n')
    private_key = lines[0].split(':')[1].strip()
    public_key = lines[1].split(':')[1].strip()
    if not private_key or not public_key:
        raise Exception('Incorrect bls keypair')
    return public_key, private_key


def execute_cmd(cmd):
    r = os.popen(cmd)
    out = r.read()
    r.close()
    return out
