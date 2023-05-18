import os

from platon_env.base.host import Host
from platon_env.utils import md5

host = Host('10.10.8.181', 'juzix', password='123456')
host2 = Host('10.10.8.182', 'juzix', password='123456')
host3 = Host('10.10.8.183', 'juzix', password='123456')
host_base_dir = '/home/juzix'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_pid():
    pid = host.pid('cpu')
    assert type(pid) is str


def test_ssh():
    host.ssh('mkdir tests')
    dir_list = host.ssh('ls')
    assert 'tests' in dir_list


def test_file_exist():
    assert host.file_exist(host_base_dir)
    assert host.file_exist(host_base_dir + "/hello") is False


def test_fast_put():
    platon_bin = os.path.join(base_dir, 'tests/file/platon')
    tmp_file = host.fast_put(platon_bin)
    tem_dir, md5_value = tmp_file.split('/')[0], tmp_file.split('/')[1]
    assert tem_dir == host.tmp_dir and md5_value == md5(platon_bin)

    result = host.fast_put(os.path.join(base_dir, 'tests/file/platon'), 'platon_evn/platon')
    assert result is None


def test_concurrent_fast_put():
    local = os.path.join(base_dir, 'tests/file/genesis.json')
    remote = host_base_dir + '/fast_put_debug/genesis.json'
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
