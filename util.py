import os


def check_file_exists(*args):
    """can_deploy
    Check if local files exist
    :param args:
    """
    for arg in args:
        if not os.path.exists(os.path.abspath(arg)):
            raise Exception("file:{} does not exist".format(arg))


def run_ssh(ssh, cmd, password=None):
    stdin, stdout, _ = ssh.exec_command(rf'source /etc/profile; {cmd}')
    if password:
        stdin.write(password + '\n')
    return stdout.readlines()
