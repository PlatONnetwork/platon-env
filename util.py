import os
import hashlib


def check_file_exists(*args):
    """can_deploy
    Check if local files exist
    :param args:
    """
    for arg in args:
        if not os.path.exists(os.path.abspath(arg)):
            raise Exception("file:{} does not exist".format(arg))


def md5(file):
    with open(file, 'rb') as f:
        m5 = hashlib.md5()
        m5.update(f.read())
    return m5.hexdigest()
