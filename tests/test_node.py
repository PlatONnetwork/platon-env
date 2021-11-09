import pytest

from base.host import Host
from platon.genesis import Genesis
from platon.node import Node, NodeOpts

# from utils.util import CMD

# host = Host('10.10.8.209', 'juzhen', '123456')
# node_id = '35bb5daad814fe902030cba6fd2d3ec60906dab70ba5df4d42a19448d300ab203cfd892c325f6716965dd93d8de2a377a2806c9703b69b68287577c70f9e7c07'
# node_key = '0db2cc59f8d87beb65d5ebd56c9beb9f316a406918f66679b638ebd78bb695e1'
# host = Host('192.168.16.121', 'juzix', password='123456')

# genesis_file = 'file/genesis.json'

node_id = '493c66bd7d6051e42a68bffa5f70005555886f28a0d9f10afaca4abc45723a26d6b833126fb65f11e3be51613405df664e7cda12baad538dd08b0a5774aa22cf'
node_key = '3f9301b1e574ce779e3d4ba054f3275e3a7d6d2ab22d1ef4b6b94e1b1491b55f'
network = 'private'

bls_pubKey = '5b6ce2480feee69b2007516054a25ace5d7ea2026d271fbdadcc2266f9e21e3e912f7d770c85f45385ba44e673e22b0db5ef5af1f57adf75d9b1b7628748d33a4a57ee2c8c7236691e579d219d42e1d875e084359acb8231fbc3da8ae400200e'
bls_prikey = 'edc1eafa379dadbe39297b629d0e17a4c7c3d90d8b7d08795a7db79dd498ec36'

genesis_file = r'C:\PlatON\PlatON_code\platon-env\tests\file\genesis.json'
genesis = Genesis(genesis_file)
genesis.fill_init_nodes(content=[
                {
                    "node": "enode://493c66bd7d6051e42a68bffa5f70005555886f28a0d9f10afaca4abc45723a26d6b833126fb65f11e3be51613405df664e7cda12baad538dd08b0a5774aa22cf@192.168.21.42:16789",
                    "blsPubKey": "5b6ce2480feee69b2007516054a25ace5d7ea2026d271fbdadcc2266f9e21e3e912f7d770c85f45385ba44e673e22b0db5ef5af1f57adf75d9b1b7628748d33a4a57ee2c8c7236691e579d219d42e1d875e084359acb8231fbc3da8ae400200e"
                }])

genesis.save(genesis_file)

base_dir = '/home/shing'
host = Host('192.168.21.42', 'shing', password='aa123456')
node = Node(host, node_id, node_key, network, bls_pubkey=bls_pubKey, bls_prikey=bls_prikey, base_dir=base_dir)
rpc_port = '6789'
rpc_api = 'web3,platon,admin,personal,debug'
platon = 'file/platon'
keystore_dir = 'file/keystore.tar.gz'

@pytest.fixture()
def install_node():
    nodeOpts = NodeOpts(rpc_port=rpc_port, rpc_api=rpc_api, ws_port=None, ws_api=None, extra_opts=None)
    node.install(platon=platon, network=network, genesis_file=genesis_file, static_nodes=node.static_nodes,
                 keystore_dir=keystore_dir, options=nodeOpts)

    return node



def test_enode():
    enode_info = node.enode
    assert enode_info == r'enode://' + node_id + "@" + node.host.ip + ":" + str(node.p2p_port)



def test_install():
    platon = 'file/platon'
    # genesis_file = 'file/genesis.json'
    keystore_dir = 'file/keystore.tar.gz'
    # cmd = CMD(6789, 'platon,txpool,admin,debug')
    nodeOpts = NodeOpts(rpc_port=rpc_port, rpc_api=rpc_api, ws_port=None, ws_api=None, extra_opts=None)
    node.install(platon=platon, network=network, genesis_file=genesis_file, static_nodes=node.static_nodes,
                 keystore_dir=keystore_dir, options=nodeOpts)
    pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
    assert pid != '' and int(pid) > 0


def test_uninstall(install_node):
    pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
    assert pid != '' and int(pid) > 0
    ls = host.ssh(f'cd {base_dir};ls')
    assert node.name in ls
    supervisor_cfg = host.ssh(f'cd {host.supervisor.process_config_path};ls')
    assert node.name + '.conf' == supervisor_cfg

    node.uninstall()
    pid_after = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
    assert pid_after == ''
    ls_after = host.ssh(f'cd {base_dir};ls')
    assert node.name not in ls_after
    supervisor_cfg_after = host.ssh(f'cd {host.supervisor.process_config_path};ls')
    assert node.name not in supervisor_cfg_after


def test_status(install_node):
    status = node.status()
    assert status is True
    status_restart = node.status()
    assert status_restart is True
    node.stop()
    status_stop = node.status()
    assert status_stop is False

def test_start():
    # install里面包含，且不太好写，就不重复写了。
    # node.start()
    pass

def test_init():
    # install里面包含，且不太好写，就不重复写了。
    # node.init()
    pass

def test_restart(install_node):
    pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
    assert pid != '' and int(pid) > 0
    node.restart()
    pid_restart = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
    assert pid_restart != '' and pid_restart != pid



def test_stop(install_node):
    pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
    assert pid != '' and int(pid) > 0
    node.stop()
    pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
    assert pid == ''


def test_upload_platon():
    node.uninstall()
    node.upload_platon(platon)
    ls_after = host.ssh(f'cd {node.deploy_path};ls')
    assert ls_after == 'platon'

def test_upload_keystore():
    # dir格式的还没有写，有空再写
    node.uninstall()
    node.upload_keystore(keystore_dir)
    ls_after = host.ssh(f'cd {node.data_dir};ls')
    assert 'keystore\n' in ls_after


def test_set_static_nodes():
    node.uninstall()
    enodes = [
    "enode://3ea97e7d098d4b2c2cc7fb2ef9e2c1b802d27f01a4a0d1f7ca5ab5ce2133d560c6f703f957162a580d04da59f45707dae40107c99762509278adf1501692e0a6@192.168.16.121:16789",
    "enode://c9b8de645f6060a364c35e89a4744263917e1342eb3f131e8ce6b2f81f92bb9601832a354d0a54b3ca051064329867590923fc4dbb60ea0d82219ec20a851cac@192.168.16.123:16789",
    "enode://e9ee916797e66c3e10eb272956525f62ac8f9b9b74af05a5b021c7b23d7b740359c62912fe5e7fef66f2a3f5358bc7d8c1af7d862269ed5db27b5cbcf9820ec8@192.168.16.122:16789",
    "enode://03d6f06860ace8a5295167e039b7b7161a1e8903bacf9e50fb32b1a74b15a9fc1b28b400630ef38a6fb6a0c8874dd01cd65788b42a864da56e442ab7d832d7ea@192.168.16.124:16789",
]
    node.set_static_nodes(enodes)
    ls_after = host.ssh(f'cd {node.deploy_path};ls')
    assert ls_after == 'static-nodes.json'


def test_gen_supervisor_cfg():
    config = node.supervisor_config
    assert 'program:' in config
