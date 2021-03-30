import json
import os
import shutil
import tarfile
from loguru import logger
from typing import List
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

from config import Config, NodesInfo, NodeInfo, HostInfo
from host import Host
from node import Node
from util import md5


class Chain:
    def __init__(self, nodes: NodesInfo, config: Config):
        self.config = config
        # generate node obj
        self.init_nodes = self._gen_node_obj(nodes.init.members)
        self.normal_nodes = self._gen_node_obj(nodes.normal.members)
        self.nodes = self.init_nodes + self.normal_nodes
        # generate host obj
        all_nodes = nodes.init.members + nodes.normal.members
        self.hosts = self._gen_host_obj(all_nodes)
        self.res_id = md5(self.config.platon)

    def get_node(self, node_id):
        """ Get the node object by node id.
        """
        for node in self.nodes:
            if node_id == node.node_id:
                return node

    def is_running(self, nodes: List[Node] = None) -> bool:
        """ Check the running status of the nodes.
        """
        if nodes is None:
            nodes = self.nodes
        for node in nodes:
            if not node.running:
                return False
        return True

    def deploy(self, nodes: List[Node] = None):
        """ Deploy all nodes and start
        """
        if nodes is None:
            nodes = self.nodes
        self._gen_tmp_files()
        self.clean(nodes)
        self._install_dependency(nodes)
        self._install_supervisor(nodes)
        self._upload_node_files(nodes)
        self._upload_host_files(nodes)
        self.start(nodes)
        self.is_running(nodes)

    def start(self, nodes: List[Node] = None):
        """ Boot node
        """
        if nodes is None:
            nodes = self.nodes

        def _start(node: Node):
            return node.start()

        return self._concurrent_executor(_start, nodes)

    def stop(self, nodes: List[Node] = None):
        """ Close node
        """
        if nodes is None:
            nodes = self.nodes

        def _stop(node: Node):
            return node.stop()

        return self._concurrent_executor(_stop, nodes)

    def restart(self, nodes: List[Node] = None):
        """ Restart node
        """
        if nodes is None:
            nodes = self.nodes

        def _restart(node: Node):
            return node.restart()

        return self._concurrent_executor(_restart, nodes)

    def clean(self, nodes: List[Node] = None):
        """ Close the node and delete the node data
        """
        if nodes is None:
            nodes = self.nodes

        def _clean(node: Node):
            return node.clean()

        return self._concurrent_executor(_clean, nodes)

    def clean_db(self, nodes: List[Node] = None):
        """ Close the node and clear the node database
        """
        if nodes is None:
            nodes = self.nodes

        def _clean_db(node: Node):
            return node.clean_db()

        return self._concurrent_executor(_clean_db, nodes)

    def clean_supervisorctl_cfg(self, hosts: List[Host] = None):
        if hosts is None:
            hosts = self.hosts

        def clean(host: Host):
            return host.clean_supervisorctl_cfg()

        return self._concurrent_executor(clean, hosts)

    def shutdown(self, nodes: List[Node] = None):
        """ Close all nodes and delete the node deployment directory, supervisor node configuration
        """
        logger.info("shutdown and clean all nodes")
        if nodes is None:
            nodes = self.nodes

        def _shutdown(node: Node):
            return node.close()

        return self._concurrent_executor(_shutdown, nodes)

    def _gen_node_obj(self, nodes_info: List[NodeInfo]):
        """ Instantiate all nodes to class 'Node'
        """
        nodes = []
        for node_info in nodes_info:
            nodes.append(Node(node_info, self.config))
        return nodes

    def _gen_host_obj(self, hosts_info: List[HostInfo]) -> List[Host]:
        """ Instantiate all Hosts
        """
        hosts, done = [], []
        for host_info in hosts_info:
            if host_info.host in done:
                continue
            done.append(host_info.host)
            hosts.append(Host(host_info, self.config))
        return hosts

    def _gen_genesis_nodes(self, nodes: List[Node] = None) -> List[dict]:
        """ genesis the genesis node list
        """
        if nodes is None:
            nodes = self.init_nodes
        genesis_nodes = []
        for node in nodes:
            genesis_nodes.append({"node": node.enode, "blsPubKey": node.bls_pubkey})
        return genesis_nodes

    def _gen_static_nodes(self, nodes: List[Node] = None) -> list:
        """ Get static node list
        """
        if nodes is None:
            nodes = self.init_nodes
        static_nodes = []
        for node in nodes:
            static_nodes.append(node.enode)
        return static_nodes

    def _gen_tmp_files(self):
        if not os.path.exists(self.config.local_tmp_dir):
            os.mkdir(self.config.local_tmp_dir)
        self._fill_genesis_file()
        self._fill_static_file()
        self._tar_files_to_local_tmp(self.config.platon)
        self._tar_files_to_local_tmp(self.config.keystore_dir)

    def _fill_genesis_file(self):
        """ fill genesis file
        """
        if self.config.network is 'private':
            if not self.config.genesis_file:
                raise FileNotFoundError('genesis template file not found!')
        with open(self.config.genesis_file, mode='r', encoding='utf-8') as f:
            genesis_dict = json.load(f)
        init_nodes = genesis_dict['config']['cbft']['initialNodes']
        genesis_nodes = self._gen_genesis_nodes(self.init_nodes)
        # TODO: 补充异常提示
        if bool(init_nodes) == bool(genesis_nodes):
            raise Exception('The init node already exist in the genesis file, but it is different from the chain file.')
        genesis_dict['config']['cbft']['initialNodes'] = genesis_nodes
        tmp_file = os.path.join(self.config.local_tmp_dir, 'genesis.json')
        with open(tmp_file, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(genesis_dict, indent=4))

    def _fill_static_file(self):
        """ Rewrite static
        """
        if not self.config.static_nodes:
            self.config.static_nodes = self._gen_static_nodes()
        tmp_file = os.path.join(self.config.local_tmp_dir, 'static-nodes.json')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.config.static_nodes, indent=4))

    def _tar_files_to_local_tmp(self, files):
        """ Compression files
        """
        files_md5 = md5(files)
        tmp_file = os.path.join(self.config.local_tmp_dir, files_md5)
        if os.path.exists(tmp_file):
            return
        os.makedirs(tmp_file)
        shutil.copyfile(self.config.platon, os.path.join(tmp_file, "platon"))
        t = tarfile.open(tmp_file + ".tar.gz", "w:gz")
        t.add(tmp_file, arcname=os.path.basename(tmp_file))
        t.close()

    def _upload_host_files(self, hosts: List[Host] = None):
        """ Upload tmp file to hosts
        """

        def uploads(host: Host):
            return host._upload_file()

        return self._concurrent_executor(uploads, self.hosts)

    def _upload_node_files(self, nodes: List[Node] = None):
        """ Upload node config file to nodes
        """
        if nodes is None:
            nodes = self.nodes

        def uploads(node: Node):
            return node._upload_files()

        return self._concurrent_executor(uploads, nodes)

    def _install_dependency(self, hosts: List[Host] = None):
        """ Installation dependence
        """
        if hosts is None:
            hosts = self.hosts

        def install(host: Host):
            return host.__install_dependency()

        return self._concurrent_executor(install, hosts)

    def _install_supervisor(self, hosts: List[Host] = None):
        """ Install supervisor
        """
        if hosts is None:
            hosts = self.hosts

        def install(host: Host):
            return host.__install_supervisor()

        return self._concurrent_executor(install, hosts)

    def _concurrent_executor(self, func, objs, *args) -> bool:
        with ThreadPoolExecutor(max_workers=self.config.max_threads) as exe:
            futures = [exe.submit(func, pair, *args) for pair in objs]
            done, unfinished = wait(futures, timeout=30, return_when=ALL_COMPLETED)
        result = []
        for d in done:
            is_success, msg = d.result()
            if not is_success:
                result.append(msg)
        if len(result) > 0:
            raise Exception("executor {} failed:{}".format(func.__name__, result))
        return True

    # def __gen_env_id(self) -> str:
    #     """
    #     """
    #     env_tmp_file = os.path.join(self.cfg.env_tmp, "env.yml")
    #     if os.path.exists(self.cfg.env_tmp):
    #         if os.path.exists(env_tmp_file):
    #             env_data = LoadFile(env_tmp_file).get_data()
    #             if env_data["bin_hash"] == calc_hash(self.cfg.bin_file) \
    #                     and env_data["node_hash"] == calc_hash(self.cfg.node_file):
    #                 return env_data["env_id"]
    #         shutil.rmtree(self.cfg.env_tmp)
    #     os.makedirs(self.cfg.env_tmp)
    #     new_env_data = {"bin_hash": calc_hash(self.cfg.bin_file), "node_hash": calc_hash(self.cfg.node_file)}
    #     env_id = new_env_data["bin_hash"] + new_env_data["node_hash"]
    #     new_env_data["env_id"] = env_id
    #     with open(env_tmp_file, "w", encoding="utf-8") as f:
    #         yaml.dump(new_env_data, f, Dumper=yaml.RoundTripDumper)
    #     return env_id

    # def __check_log_path(self):
    #     if not os.path.exists(self.cfg.tmp_log):
    #         os.mkdir(self.cfg.tmp_log)
    #     else:
    #         shutil.rmtree(self.cfg.tmp_log)
    #         os.mkdir(self.cfg.tmp_log)
    #     if not os.path.exists(self.cfg.bug_log):
    #         os.mkdir(self.cfg.bug_log)

# def create_env(conf_tmp=None, node_file=None, account_file=None, init_chain=True,
#                install_dependency=False, install_supervisor=False) -> Controller:
#     if not conf_tmp:
#         conf_tmp = DEFAULT_CONF_TMP_DIR
#     else:
#         conf_tmp = ConfTmpDir(conf_tmp)
#     cfg = TestConfig(conf_tmp=conf_tmp, install_supervisor=install_supervisor, install_dependency=install_dependency, init_chain=init_chain)
#     if node_file:
#         cfg.node_file = node_file
#     if account_file:
#         cfg.account_file = account_file
#     return Controller(cfg)
