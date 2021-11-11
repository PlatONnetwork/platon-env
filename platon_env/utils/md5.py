import hashlib


def md5(file):
    with open(file, 'rb') as f:
        m5 = hashlib.md5()
        m5.update(f.read())
    return m5.hexdigest()
