import json
import os
import shutil
import tarfile
from loguru import logger
from typing import List
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from config import Config, NodesInfo, NodeInfo
from host import Host
from node import Node
from util import md5


class Chain:
    def __init__(self, nodes: NodesInfo, config: Config):
        self.config = config
        # generate node obj
        self.init_nodes = self.__gen_node_obj(nodes.init.members)
        self.normal_nodes = self.__gen_node_obj(nodes.normal.members)
        self.nodes = self.init_nodes + self.normal_nodes
        # generate host obj
        all_nodes = nodes.init.members + nodes.normal.members
        self.hosts = self.__gen_host_obj(all_nodes)
        self.res_id = md5(self.config.platon)

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
        self.gen_tmp_files()
        self.install_dependency()   # todo: 支持多节点
        self.clean(nodes)
        self.upload_files(nodes)
        self.start(nodes)
        self.is_running(nodes)

    def gen_tmp_files(self):
        if not os.path.exists(self.config.local_tmp_dir):
            os.mkdir(self.config.local_tmp_dir)
        self.__fill_genesis_file()
        self.__fill_static_file()
        self.__save_files_to_tmp(self.config.platon)
        self.__save_files_to_tmp(self.config.keystore_dir)

    def start(self, nodes: List[Node] = None):
        """ Boot node
        """
        if nodes is None:
            nodes = self.nodes

        def _start(node: Node):
            return node.start()

        return self.executor(_start, nodes)

    def stop(self, nodes: List[Node] = None):
        """ Close node
        """
        if nodes is None:
            nodes = self.nodes

        def _stop(node: Node):
            return node.stop()

        return self.executor(_stop, nodes)

    def restart(self, nodes: List[Node] = None):
        """ Restart node
        """
        if nodes is None:
            nodes = self.nodes

        def _restart(node: Node):
            return node.restart()

        return self.executor(_restart, nodes)

    def clean(self, nodes: List[Node] = None):
        """ Close the node and delete the node data
        """
        if nodes is None:
            nodes = self.nodes

        def _clean(node: Node):
            return node.clean()

        return self.executor(_clean, nodes)

    def clean_db(self, nodes: List[Node] = None):
        """ Close the node and clear the node database
        """
        if nodes is None:
            nodes = self.nodes

        def _clean_db(node: Node):
            return node.clean_db()

        return self.executor(_clean_db, nodes)

    def shutdown(self, nodes: List[Node] = None):
        """ Close all nodes and delete the node deployment directory, supervisor node configuration
        """
        logger.info("shutdown and clean all nodes")
        if nodes is None:
            nodes = self.nodes

        def close(node: Node):
            return node.close()

        return self.executor(close, nodes)

    def clean_supervisor_file(self, hosts: List[Host] = None):
        if hosts is None:
            hosts = self.hosts

        def clean(host: Host):
            return host.clean_supervisor_cfg()

        return self.executor(clean, hosts)

    def get_node(self, node_id):
        """ Get the node object by node id.
        """
        for node in self.nodes:
            if node_id == node.node_id:
                return node

    def upload_files(self, nodes: List[Node] = None):
        """ Upload s files
        """
        self.__put_files()
        if nodes is None:
            nodes = self.nodes

        def _upload_files(node: Node):
            return node.upload_files()

        return self.executor(_upload_files, nodes)

    def __put_files(self, hosts: List[Host] = None):
        """ Upload compressed file
        """
        def uploads(host: Host):
            return host.upload_file()

        return self.executor(uploads, self.hosts)

    def __gen_host_obj(self, nodes_info: List[NodeInfo]) -> List[Host]:
        """ Instantiate all Hosts
        """
        hosts, done = [], []
        for node_info in nodes_info:
            if node_info.host in done:
                continue
            done.append(node_info.host)
            hosts.append(Host(node_info, self.config))
        return hosts

    def __fill_static_file(self):
        """ Rewrite static
        """
        if not self.config.static_nodes:
            self.config.static_nodes = self.__gen_static_nodes()
        tmp_file = os.path.join(self.config.local_tmp_dir, 'static-nodes.json')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.config.static_nodes, indent=4))

    def __save_files_to_tmp(self, files):
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

    def __gen_node_obj(self, nodes_info: List[NodeInfo]):
        """ Instantiate all nodes to class 'Node'
        """
        nodes = []
        for node_info in nodes_info:
            nodes.append(Node(node_info, self.config))
        return nodes

    def __fill_genesis_file(self):
        """ fill genesis file
        """
        if self.config.network is 'private':
            if not self.config.genesis_file:
                raise FileNotFoundError('genesis template file not found!')
        with open(self.config.genesis_file, mode='r', encoding='utf-8') as f:
            genesis_dict = json.load(f)
        init_nodes = genesis_dict['config']['cbft']['initialNodes']
        genesis_nodes = self.__gen_genesis_nodes(self.init_nodes)
        # TODO: 补充异常提示
        if bool(init_nodes) == bool(genesis_nodes):
            raise Exception('The init node already exist in the genesis file, but it is different from the chain file.')
        genesis_dict['config']['cbft']['initialNodes'] = genesis_nodes
        tmp_file = os.path.join(self.config.local_tmp_dir, 'genesis.json')
        with open(tmp_file, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(genesis_dict, indent=4))

    def __gen_genesis_nodes(self, nodes: List[Node]) -> List[dict]:
        """ genesis the genesis node list
        """
        genesis_nodes = []
        for node in nodes:
            genesis_nodes.append({"node": node.enode, "blsPubKey": node.bls_pubkey})
        return genesis_nodes

    def __gen_static_nodes(self) -> list:
        """ Get static node enode list
        """
        static_nodes = []
        for node in self.nodes:
            static_nodes.append(node.enode)
        return static_nodes

    def executor(self, func, objs, *args) -> bool:
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

    def install_dependency(self, hosts: List[Host] = None):
        if self.config.install_dependency:
            self.__install_supervisor_all()
            self.__install_dependency_all()
            self.config.install_dependency = False

    def __install_dependency_all(self):
        """ Installation dependence
        """

        def install(host: Host):
            return host.install_dependency()

        return self.executor(install, self.hosts)

    def __install_supervisor_all(self):
        """ Install supervisor
        """

        def install(host: Host):
            return host.install_supervisor()

        return self.executor(install, self.hosts)



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

