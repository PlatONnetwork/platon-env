import json
import os
import time
import shutil
import tarfile

from ruamel import yaml
from typing import List

# import genesis
# from funcs.load_file import LoadFile, calc_hash
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from config import Config, Nodes
from host import Host
from node import Node


class Chain:
    def __init__(self, config: Config, nodes: Nodes):
        self.config = config
        if not os.path.exists(self.config.deploy.local_tmp_dir):
            os.mkdir(self.config.deploy.local_tmp_dir)
        # generate node obj
        self.init_nodes = self.__gen_node_obj(nodes.init.members)
        self.normal_nodes = self.__gen_node_obj(nodes.normal.members)
        self.nodes = self.init_nodes + self.normal_nodes
        # generate host obj
        self.hosts = self.__gen_host_obj()
        # fill genesis file
        self.init_chain = False

        if self.ciself.config.chain.genesis:
            self.init_chain = True
            self.__fill_genesis_file()

        # 生成环境唯一标识
        self.env_id = self.__gen_env_id()

    def is_running(self, nodes: List[Node]) -> bool:
        """ Check the running status of the nodes.
        """
        if nodes is None:
            nodes = self.nodes
        for node in nodes:
            if not node.running:
                return False
        return True

    def get_node(self, node_id):
        """ Get the node object by node id.
        """
        for node in self.nodes:
            if node_id == node.node_id:
                return node

    def deploy(self, nodes: List[Node]):
        """ Deploy all nodes and start
        """
        if nodes is None:
            nodes = self.nodes
        self.clean(nodes)
        self.gen_tmp_files()
        self.install_dependency()
        self.upload_files(nodes)
        self.start(nodes)
        self.is_running(nodes)

    def gen_tmp_files(self):
        """ Prepare environmental data
        """
        self.__fill_genesis_file()
        self.__fill_static_file()
        self.__compression_files()

    def install_dependency(self):
        if self.init_dependency:
            self.__install_supervisor_all()
            self.__install_dependency_all()
            self.init_dependency = False

    def upload_files(self, nodes: List[Node] = None):
        """ Upload all files
        """
        self.__put_files_all()
        if nodes is None:
            nodes = self.nodes

        def _upload_files(node: Node):
            return node.upload_files()

        return self.executor(_upload_files, nodes)

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

    def clean_supervisor_file(self, hosts: List[Host] = None):
        if hosts is None:
            hosts = self.hosts

        def clean(host: Host):
            return host.clean_supervisor_cfg()

        return self.executor(clean, hosts)

    def shutdown(self, nodes: List[Node] = None):
        """ Close all nodes and delete the node deployment directory, supervisor node configuration
        """
        logger.info("shutdown and clean all nodes")
        if nodes is None:
            nodes = self.nodes

        def close(node: Node):
            return node.close()

        return self.executor(close, nodes)

    def __put_files_all(self):
        """
        Upload compressed file
        """
        logger.info("upload compression")

        def uploads(host: Host):
            return host.upload_files()

        return self.executor(uploads, self.hosts)

    def __install_dependency_all(self):
        """
        Installation dependence
        """
        logger.info("install rely")

        def install(host: Host):
            return host.install_dependency()

        return self.executor(install, self.hosts)

    def __install_supervisor_all(self):
        """
        Install supervisor
        """
        logger.info("install supervisor")

        def install(host: Host):
            return host.install_supervisor()

        return self.executor(install, self.hosts)

    def __gen_host_obj(self) -> List[Host]:
        """ Instantiate all Hosts
        """
        hosts, hosts_info, done = [], [], []
        for node_info in self.__nodes_info:
            if node_info['host'] in done:
                continue
            hosts_info.append(node_info)
            done.append(node_info['host'])
        for host_info in hosts_info:
            hosts.append(Host(host_info))
        return hosts

    def __fill_static_file(self):
        """
        Rewrite static
        """
        logger.info("rewrite static-nodes.json")
        static_nodes = self.__gen_static_nodes()
        with open(config.TMP_STATIC_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(static_nodes, indent=4))

    def __compression_files(self):
        """ Compressed file
        """
        env_gz = os.path.join(config.TMP_DIR, self.env_id)
        if os.path.exists(env_gz):
            return
        os.makedirs(env_gz)
        data_dir = os.path.join(env_gz, "data")
        os.makedirs(data_dir)
        keystore_dir = os.path.join(data_dir, "keystore")
        os.makedirs(keystore_dir)
        shutil.copy(config.KEYSTORE_DIR, keystore_dir)
        shutil.copyfile(config.BIN_FILE, os.path.join(env_gz, "platon"))
        t = tarfile.open(env_gz + ".tar.gz", "w:gz")
        t.add(env_gz, arcname=os.path.basename(env_gz))
        t.close()

    def download_log(self, mark, nodes: List[Node] = None):
        """ Download log
        """
        # self.__check_log_path()
        if nodes is None:
            nodes = self.nodes

        def download(node: Node):
            return node.download_log()

        self.executor(download, nodes)
        return self.__zip_all_log(mark)

    # TODO: delete
    # def __zip_all_log(self, mark):
    #     logger.info("Start compressing.....")
    #     t = time.strftime("%Y%m%d%H%M%S", time.localtime())
    #     tar_name = "{}/{}_{}.tar.gz".format(self.config.NODE_LOG_DIR, mark, t)
    #     tar = tarfile.open(tar_name, "w:gz")
    #     tar.add(config.tmp_log, arcname=os.path.basename(self.cfg.NODE_LOG_DIR))
    #     tar.close()
    #     logger.info("Compression completed")
    #     logger.info("Start deleting the cache.....")
    #     shutil.rmtree(self.cfg.tmp_log)
    #     logger.info("Delete cache complete")
    #     return os.path.basename(tar_name)



    def __gen_node_obj(self, nodes_info: list):
        """ Instantiate all nodes to class 'Node'
        """
        nodes = []
        for node_info in nodes_info:
            nodes.append(Node(node_info, self.chain_id))
        return nodes

    def __fill_genesis_file(self):
        """ Rewrite genesis
        """
        with open(self.config.genesis_file, mode='r', encoding='utf-8') as f:
            self.genesis = genesis.genesis_factory(json.load(f))
        nodes = self.genesis.config.cbft.initialNodes
        genesis_nodes = self.__gen_genesis_nodes()
        if bool(nodes) == bool(genesis_nodes):
            raise Exception('The init node already exist in the genesis file, but it is different from the chain file.')
        self.genesis.config.cbft.initialNodes = genesis_nodes
        with open(self.config.tmp_genesis_file, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(self.genesis.to_dict(), indent=4))

    def __gen_genesis_nodes(self) -> List[dict]:
        """ genesis the genesis node list
        """
        genesis_nodes = []
        for node in self.init_nodes:
            genesis_nodes.append({"node": node.enode, "blsPubKey": node.bls_pubkey})
        return genesis_nodes

    def __gen_static_nodes(self) -> list:
        """ Get static node enode list
        """
        static_nodes = []
        for node in self.nodes:
            static_nodes.append(node.enode)
        return static_nodes

    def __gen_env_id(self) -> str:
        """
        Determine whether you need to re-create a new environment
        based on the platon binary information and the node configuration file.
        :return: env_id
        """
        env_tmp_file = os.path.join(self.cfg.env_tmp, "env.yml")
        if os.path.exists(self.cfg.env_tmp):
            if os.path.exists(env_tmp_file):
                env_data = LoadFile(env_tmp_file).get_data()
                if env_data["bin_hash"] == calc_hash(self.cfg.bin_file) \
                        and env_data["node_hash"] == calc_hash(self.cfg.node_file):
                    return env_data["env_id"]
            shutil.rmtree(self.cfg.env_tmp)
        os.makedirs(self.cfg.env_tmp)
        new_env_data = {"bin_hash": calc_hash(self.cfg.bin_file), "node_hash": calc_hash(self.cfg.node_file)}
        env_id = new_env_data["bin_hash"] + new_env_data["node_hash"]
        new_env_data["env_id"] = env_id
        with open(env_tmp_file, "w", encoding="utf-8") as f:
            yaml.dump(new_env_data, f, Dumper=yaml.RoundTripDumper)
        return env_id

    # def __check_log_path(self):
    #     if not os.path.exists(self.cfg.tmp_log):
    #         os.mkdir(self.cfg.tmp_log)
    #     else:
    #         shutil.rmtree(self.cfg.tmp_log)
    #         os.mkdir(self.cfg.tmp_log)
    #     if not os.path.exists(self.cfg.bug_log):
    #         os.mkdir(self.cfg.bug_log)

    def executor(self, func, objs, *args) -> bool:
        with ThreadPoolExecutor(max_workers=config.MAX_THREADS) as exe:
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

from loguru import logger

if __name__ == "main":
    pass
    # logger.
