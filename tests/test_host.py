from platon_env.base.host import Host

# host = Host('10.10.8.209', 'juzhen', 'Juzhen123!')
from platon_env.utils.md5 import md5

# host = Host('192.168.16.121', 'juzix', password='123456')
host = Host('192.168.120.121', 'platon', password='Platon123!')
host2 = Host('192.168.120.121', 'platon', password='Platon123!')
host3 = Host('192.168.120.121', 'platon', password='Platon123!')
base_dir = '/home/platon'


def test_pid():
    pid = host.pid('cpu')
    assert type(pid) is str


def test_ssh():
    host.ssh('mkdir tests')
    dir_list = host.ssh('ls')
    assert 'tests' in dir_list


def test_file_exist():
    assert host.file_exist(base_dir)
    assert host.file_exist(base_dir + "/hello") is False


def test_fast_put():
    platon_bin = 'file/platon'
    tmp_file = host.fast_put(platon_bin)
    tem_dir, md5_value = tmp_file.split('/')[0], tmp_file.split('/')[1]
    assert tem_dir == host.tmp_dir and md5_value == md5(platon_bin)

    result = host.fast_put('file/platon', 'platon_evn/platon')
    assert result is None


def test_concurrent_fast_put():
    local = 'file/genesis.json'
    remote = base_dir + '/fast_put_debug/genesis.json'
    hosts = [host, host2, host3]

    from platon_env.utils.executor import concurrent_executor
    concurrent_executor(hosts, 'fast_put', local, remote)


def test_write_file():
    result = host.write_file('hello world', '/home/juzix/test.txt')
    assert result is None


def test_register():
    pass


def test_unregister():
    pass


def test_get_processes():
    pass


def test_set_supervisor():
    pass
