from base.service import Service


class server:

    def __init__(self, ip, username, password=None, services: [Service]=None):
        self.ip = None
        self.username = None
        self.password = None
        self.certificate = None
        self.certificate_password = None
        self.connection_type = None     # 免密/密码/证书/所有
        self.add_services(services)
        self.services: list = services

    def add_services(self, services: [Service]):
        # 添加服务， 同名服务会抛出异常
        for service in services:
            setattr(self, service.name, service)
            self.services.append(service)

    def remove_services(self, services: [Service]):
        pass



