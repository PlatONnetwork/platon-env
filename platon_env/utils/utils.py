import hashlib
import os
import tarfile

from threading import Event

event = Event()


def do_once(func, *args, **kwargs):
    if event.is_set():
        event.wait()
    else:
        event.set()
        func(*args, **kwargs)
        event.clear()


def md5(file):
    with open(file, 'rb') as f:
        m5 = hashlib.md5()
        m5.update(f.read())
    return m5.hexdigest()


def join_path(*keys, split='/'):
    return split.join(keys)


def tar_files(source, dest):
    tar = tarfile.open(dest, 'w:gz')
    tar.add(source, arcname=os.path.basename(source))
    tar.close()
