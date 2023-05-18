from platon_env.genesis import Genesis
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
genesis_file = os.path.join(base_dir, 'tests/file/genesis.json')
genesis = Genesis(genesis_file)
enode = "enode://493c66bd7d6051e42a68bffa5f70005555886f28a0d9f10afaca4abc45723a26d6b833126fb65f11e3be51613405df664e7cda12baad538dd08b0a5774aa22cf@10.10.8.182:16789"
blsPubKey = "5b6ce2480feee69b2007516054a25ace5d7ea2026d271fbdadcc2266f9e21e3e912f7d770c85f45385ba44e673e22b0db5ef5af1f57adf75d9b1b7628748d33a4a57ee2c8c7236691e579d219d42e1d875e084359acb8231fbc3da8ae400200e"


def test_fill_init_nodes_and_save():
    genesis.fill_init_nodes(content=[])
    genesis.save_as(genesis_file)
    assert genesis.data['config']['cbft']['initialNodes'] == []
    genesis.fill_init_nodes(content=[
        {
            "node": enode,
            "blsPubKey": blsPubKey
        }
    ])
    genesis.save_as(genesis_file)
    assert genesis.data['config']['cbft']['initialNodes'][0]['node'] == enode
    assert genesis.data['config']['cbft']['initialNodes'][0]['blsPubKey'] == blsPubKey


def test_fill_accounts():
    genesis.fill_accounts(accounts={})
    genesis.save_as(genesis_file)
    assert genesis.data['alloc'] == {}
    accounts = {
        "0x15866368698d0f2c307E98F9723065B982e61793": {
            "balance": "100000000000000000000000000"
        },
        "0x1000000000000000000000000000000000000003": {
            "balance": "2000000000000000000000000"
        },
        "0x83d935fe68270CBC3eb093d700F8F4832D3B280D": {
            "balance": "0"
        }
    }
    genesis.fill_accounts(accounts)
    genesis.save_as(genesis_file)
    assert genesis.data['alloc'] == accounts
