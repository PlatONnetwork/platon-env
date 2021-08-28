from platon.chain import Chain
from base.host import Host
from platon.node import Node

host = Host('10.10.8.209', 'juzhen', 'Juzhen123!')
node_id = '35bb5daad814fe902030cba6fd2d3ec60906dab70ba5df4d42a19448d300ab203cfd892c325f6716965dd93d8de2a377a2806c9703b69b68287577c70f9e7c07'
node_key = '0db2cc59f8d87beb65d5ebd56c9beb9f316a406918f66679b638ebd78bb695e1'
node = Node(host, node_id, node_key)
chain = Chain(init_nodes=[], normal_nodes=[node])


def test_nodes():
    print(chain.nodes)


def test_start():
    chain.start()


def test_stop():
    chain.stop()


def test_concurrent_executor():
