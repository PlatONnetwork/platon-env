class CMD:

    def __init__(self, rpc_port=None, rpc_api=None, ws_port=None, ws_api=None, extra_cmd=None):
        self.rpc_port = rpc_port
        self.rpc_api = rpc_api
        self.ws_port = ws_port
        self.ws_api = ws_api
        self.extra_cmd = extra_cmd

    def to_string(self):
        string = ''
        if self.rpc_port:
            assert self.rpc_api, 'The RPC API is not defined!'
            string += f'--rpc --rpcaddr 0.0.0.0 --rpcport {self.rpc_port} --rpcapi {self.rpc_api} '
        if self.ws_port:
            assert self.ws_api, 'The WS API is not defined!'
            string += f'--ws --wsaddr 0.0.0.0 --wsport {self.rpc_port} --wsapi {self.rpc_api} '
        if self.extra_cmd:
            string += self.extra_cmd
        return string
