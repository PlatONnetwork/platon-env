from base.host import Host

host = Host('10.10.8.209', 'juzhen', 'Juzhen123!')


def test_ssh():
    result = host.ssh('ls')
    assert type(result) is str


def test_pid():
    pid = host.pid('cpu')
    assert type(pid) is str


def test_is_exist():
    assert host.file_exist('/home/juzhen/testing') is False


def test_save_to_file():
    host.write_file('shing', '/home/juzhen/test.txt')


def test_put_via_tmp():
    host.fast_put('file/platon')


def test_add_to_platon():
    pass


def test_add_to_alaya():
    pass


def test_add_to_private_chain():
    pass
