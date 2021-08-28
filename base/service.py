class Service:

    def __init__(self, host, **kwargs):
        self.name = None
        self.dir = None
        self.bin = None

    def __str__(self):
        return self.name

    def start(self):
        pass

    def stop(self):
        pass

    def restart(self):
        pass


