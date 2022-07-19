import pytest

from platon_env.chain import Chain
from platon_env.base.host import Host
from platon_env.node import Node

# node_id = '493c66bd7d6051e42a68bffa5f70005555886f28a0d9f10afaca4abc45723a26d6b833126fb65f11e3be51613405df664e7cda12baad538dd08b0a5774aa22cf'
# node_key = '3f9301b1e574ce779e3d4ba054f3275e3a7d6d2ab22d1ef4b6b94e1b1491b55f'
# network = 'private'
#
# bls_pubKey = '5b6ce2480feee69b2007516054a25ace5d7ea2026d271fbdadcc2266f9e21e3e912f7d770c85f45385ba44e673e22b0db5ef5af1f57adf75d9b1b7628748d33a4a57ee2c8c7236691e579d219d42e1d875e084359acb8231fbc3da8ae400200e'
# bls_prikey = 'edc1eafa379dadbe39297b629d0e17a4c7c3d90d8b7d08795a7db79dd498ec36'
# base_dir = '/home/shing'
# host = Host('192.168.21.42', 'shing', password='aa123456')
node = Node(host, node_id, node_key, network, bls_pubkey=bls_pubKey, bls_prikey=bls_prikey, base_dir=base_dir)
#
rpc_port = '6789'
rpc_api = 'web3,platon,admin,personal'
platon = 'file/platon'
keystore_dir = 'file/keystore.tar.gz'
genesis_file = r'C:\PlatON\PlatON_code\platon-env\tests\file\genesis.json'
# chain = Chain(nodes=[])
chain = Chain(nodes=[node])


@pytest.fixture()
def install_chain():
    nodeOpts = NodeOpts(rpc_port=rpc_port, rpc_api=rpc_api, ws_port=None, ws_api=None, extra_opts=None)
    chain.install(platon=platon, network=network, genesis_file=genesis_file, static_nodes=node.static_nodes,
                  keystore=keystore_dir, options=nodeOpts)
    pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
    assert pid != '' and int(pid) > 0

    return chain


from tests.conftset import platon, genesis_file, chain_file


def test_install_private_chain():
    chain = Chain.from_file(chain_file)
    chain.install(platon=platon, network='private', genesis_file=genesis_file)
    # for status in chain.status():
    #     assert status is True
    # pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
    # assert pid != '' and int(pid) > 0


# def test_uninstall(install_chain):
#     pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
#     assert pid != '' and int(pid) > 0
#     ls = host.ssh(f'cd {base_dir};ls')
#     assert node.name in ls
#     supervisor_cfg = host.ssh(f'cd {host.supervisor.process_config_path};ls')
#     assert node.name + '.conf' == supervisor_cfg
#
#     chain.uninstall()
#     pid_after = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
#     assert pid_after == ''
#     ls_after = host.ssh(f'cd {base_dir};ls')
#     assert node.name not in ls_after
#     supervisor_cfg_after = host.ssh(f'cd {host.supervisor.process_config_path};ls')
#     assert node.name not in supervisor_cfg_after
#
#
# def test_add_process():
#     # todo: 待写
#     chain.add_process()
#
#
# def test_status(install_chain):
#     status_list = chain.status()
#     assert status_list[0] is True
#     status_restart_list = chain.status()
#     assert status_restart_list[0] is True
#     chain.stop()
#     status_stop_list = chain.status()
#     assert status_stop_list[0] is False
#
#
# def test_init():
#     # 初始化断言怎么写呀
#     pass
#
#
# def test_start(install_chain):
#     chain.stop()
#     pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
#     assert pid == ''
#     chain.start()
#     pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
#     assert pid != '' and int(pid) > 0
#
#
# def test_restart(install_chain):
#     pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
#     assert pid != '' and int(pid) > 0
#     chain.restart()
#     pid_restart = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
#     assert pid_restart != '' and pid_restart != pid
#
#
# def test_stop(install_chain):
#     # chain.stop()
#     pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
#     assert pid != '' and int(pid) > 0
#     chain.stop()
#     pid = host.ssh(f'ps -ef | grep {node.name} | grep -v grep | ' + "awk {'print $2'}")
#     assert pid == ''
#
#
# def test_upload_platon(install_chain):
#     # 有多的节点用了多试几个
#     chain.uninstall()
#     chain.upload_platon(platon, [node])
#     ls_after = host.ssh(f'cd {node.deploy_path};ls')
#     assert ls_after == 'platon'
#
#
# def test_upload_keystore(install_chain):
#     # dir格式的还没有写，有空再写
#     # 有多的节点用了多试几个
#     chain.uninstall()
#     chain.upload_keystore(keystore_dir, [node])
#     ls_after = host.ssh(f'cd {node.data_dir};ls')
#     assert 'keystore\n' in ls_after
#
#
# def test_set_static_nodes(install_chain):
#     chain.uninstall()
#     enodes = [
#         "enode://3ea97e7d098d4b2c2cc7fb2ef9e2c1b802d27f01a4a0d1f7ca5ab5ce2133d560c6f703f957162a580d04da59f45707dae40107c99762509278adf1501692e0a6@192.168.16.121:16789",
#         "enode://c9b8de645f6060a364c35e89a4744263917e1342eb3f131e8ce6b2f81f92bb9601832a354d0a54b3ca051064329867590923fc4dbb60ea0d82219ec20a851cac@192.168.16.123:16789",
#         "enode://e9ee916797e66c3e10eb272956525f62ac8f9b9b74af05a5b021c7b23d7b740359c62912fe5e7fef66f2a3f5358bc7d8c1af7d862269ed5db27b5cbcf9820ec8@192.168.16.122:16789",
#         "enode://03d6f06860ace8a5295167e039b7b7161a1e8903bacf9e50fb32b1a74b15a9fc1b28b400630ef38a6fb6a0c8874dd01cd65788b42a864da56e442ab7d832d7ea@192.168.16.124:16789",
#     ]
#     chain.set_static_nodes(enodes, [node])
#     ls_after = host.ssh(f'cd {node.deploy_path};ls')
#     assert ls_after == 'static-nodes.json'
