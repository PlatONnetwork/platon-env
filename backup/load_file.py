import json
import yaml


class LoadFile(object):
    """
    Convert json or yaml files to python dictionary or list dictionary
    """

    def __init__(self, file):
        if file.split('.')[-1] not in ('yaml', 'yml', 'json'):
            raise Exception('the file format must be yaml or json')
        self.file = file

    def get_data(self):
        """
        call this method to get the result
        """
        if self.file.split('.')[-1] == 'json':
            return self.load_json()
        return self.load_yaml()

    def load_json(self):
        """
        Convert json file to dictionary
        """
        try:
            with open(self.file, encoding='utf-8') as f:
                result = json.load(f)
                if isinstance(result, list):
                    result = [i for i in result if i != '']
                return result
        except FileNotFoundError as e:
            raise e

    def load_yaml(self):
        """
        Convert yaml file to dictionary
        """
        try:
            with open(self.file, encoding='utf-8')as f:
                result = yaml.load(f)
                if isinstance(result, list):
                    result = [i for i in result if i != '']
                return result
        except FileNotFoundError as e:
            raise e
