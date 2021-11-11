from platon_env.base.host import Host

# host = Host('10.10.8.209', 'juzhen', 'Juzhen123!')
from platon_env.utils.md5 import md5

# host = Host('192.168.16.121', 'juzix', password='123456')
host = Host('192.168.21.42', 'shing', password='aa123456')
base_dir = '/home/shing'


def test_pid():
    pid = host.pid('cpu')
    assert type(pid) is str


def test_ssh():
    # result = host.ssh('ls')
    # assert type(result) is str
    host.ssh('mkdir tests')
    dir_list = host.ssh('ls')
    assert 'tests' in dir_list


def test_is_exist():
    assert host.file_exist(base_dir)
    assert host.file_exist(base_dir + "/hello") is False


def test_put_via_tmp():
    platon_bin = 'file/platon'
    tmp_file = host.fast_put(platon_bin)
    tem_dir, md5_value = tmp_file.split('/')[0], tmp_file.split('/')[1]
    assert tem_dir == host.tmp_dir and md5_value == md5(platon_bin)

    result = host.fast_put('file/platon', 'platon_evn/platon')
    assert result is None


def test_save_to_file():
    result = host.write_file('hello world', '/home/juzix/test.txt')
    assert result is None


def test_add_to_platon():
    pass


def test_add_to_alaya():
    pass


def test_add_to_private_chain():
    pass
