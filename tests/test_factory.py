from platon_env.chain import Chain


def test_chain_factory():
    chain = Chain.from_file('file/chain_file.yml')
    chain.install()
