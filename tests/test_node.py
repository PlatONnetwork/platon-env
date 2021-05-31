from host import Host
from node import Node
from utils.util import CMD

host = Host('10.10.8.209', 'juzhen', 'Juzhen123!')
node_id = '35bb5daad814fe902030cba6fd2d3ec60906dab70ba5df4d42a19448d300ab203cfd892c325f6716965dd93d8de2a377a2806c9703b69b68287577c70f9e7c07'
node_key = '0db2cc59f8d87beb65d5ebd56c9beb9f316a406918f66679b638ebd78bb695e1'
node = Node(host, node_id, node_key)


def test_enode():
    print(node.enode)


def test_gen_supervisor_cfg():
    node._prepare_supervisor_cfg()


def test_deploy():
    platon = 'file/platon'
    cmd = CMD(6789, 'platon,txpool,admin,debug')
    node.deploy(platon, network='private', genesis_file='file/genesis.json', cmd=cmd)


def test_start():
    node.start()


def test_restart():
    node.restart()


def test_stop():
    node.stop()


def test_clean():
    node.clean()
