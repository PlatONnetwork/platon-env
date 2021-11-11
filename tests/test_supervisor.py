from platon_env.base.host import Host
from platon_env.base.supervisor.supervisor import Supervisor

host = Host('10.10.8.209', 'juzhen', 'Juzhen123!')
supervisor = Supervisor(host)


def test_status():
    print(supervisor.status('p16789'))


def test_install():
    supervisor.install()


def test_uninstall():
    supervisor.uninstall()


def test_put_config():
    supervisor._upload_config()


def test_start():
    outs, errs = supervisor.start('p16789')
    print(outs, errs)
