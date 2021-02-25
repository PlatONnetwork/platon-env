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


def file_hash(file):
    with open(file, 'rb') as f:
        sha1obj = hashlib.sha1()
        sha1obj.update(f.read())
        result_hash = sha1obj.hexdigest()
        return result_hash