import hashlib


def file_hash(file):
    with open(file, 'rb') as f:
        sha1obj = hashlib.sha1()
        sha1obj.update(f.read())
        result_hash = sha1obj.hexdigest()
        return result_hash
