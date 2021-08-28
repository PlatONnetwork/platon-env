from base.host import Host

host = Host('10.10.8.209', 'juzhen', 'Juzhen123!')


def test_pwd():
    assert host.pwd() == f'/home/{host.username}'


def test_is_exist():
    assert host.is_exist('test/test.test') == False


def test_get_abs_path():
    assert host.get_abs_path('test') == f'/home/{host.username}/test'


def test_cmd():
    outs, _ = host.cmd("ps -ef | grep supervisord")
    print(outs)


def test_get_file():
    pass


def test_put_file():
    host.sftp.put('file/platon', '/home/juzhen/platon/tmp/dd5490288710cf26e022fb1446e8cbce')


def test_fast_put_file():
    pass


