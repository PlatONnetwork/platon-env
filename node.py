import os
from functools import wraps
from loguru import logger

from config import Config, Node as NodeInfo
from host import Host

failed_msg = r'p{} do {} failed:{}'
success_msg = r'p{} do {} success'


class Node(Host):
    def __init__(self, node_info: NodeInfo, config: Config):
        super().__init__(node_info, config)
        self.p2p_port = node_info.p2p_port
        self.rpc_port = node_info.rpc_port
        self.ws_port = node_info.ws_port
        # TODO: fill node info
        self.node_id = node_info.node_id
        self.node_key = node_info.node_key
        self.bls_pubkey = node_info.bls_pubkey
        self.bls_prikey = node_info.bls_prikey
        self.node_name = f'p{self.p2p_port}'
        self.node_site = f'{self.host}:{self.p2p_port}'
        self.enode = rf'enode://{self.node_id}@{self.host}:{self.p2p_port}'
        # remote deploy info
        if os.path.isabs(self.config.deploy_dir):
            self.node_dir = os.path.join(self.config.deploy_dir, self.node_name)
        else:
            self.node_dir = os.path.join(os.path.join(self.password, self.config.deploy_dir), self.node_name)
        self.log_dir = os.path.join(self.node_dir, 'log')
        self.bin_file = os.path.join(self.node_dir, 'platon')
        self.genesis_file = os.path.join(self.node_dir, 'genesis.json')
        self.config_file = os.path.join(self.node_dir, 'config.json')
        self.data_dir = os.path.join(self.node_dir, 'data')
        self.db_dir = os.path.join(self.data_dir, 'platon')
        self.keystore_dir = os.path.join(self.db_dir, 'keystore')
        self.nodekey_file = os.path.join(self.node_dir, 'nodekey')
        self.blskey_file = os.path.join(self.node_dir, 'blskey')
        self.static_file = os.path.join(self.node_dir, 'static-nodes.json')
        self.supervisor_dir = os.path.join(self.node_dir, 'supervisor')
        self.supervisor_file = os.path.join(self.supervisor_dir, self.node_name + '.conf')
        # node local tmp
        self.local_tmp_dir = os.path.join(self.config.local_tmp_dir, self.host + '_' + str(self.p2p_port))

    @property
    def running(self) -> bool:
        return bool(self.run_ssh(f"ps -ef|grep platon|grep port|grep {self.p2p_port}|grep -v grep|awk {'print $2'}"))

    # # TODO:delete
    # def make_remote_dir(self):
    #     self.run_ssh('mkdir -p {}'.format(self.node_dir))
    #     self.run_ssh('mkdir -p {}/log'.format(self.node_dir))
    #     self.run_ssh('mkdir -p {}'.format(self.data_dir))
    #     self.run_ssh('mkdir -p {}'.format(self.keystore_dir))
    #
    # # TODO:delete
    # def make_local_dir(self):
    #     if not os.path.exists(self.local_tmp_dir):
    #         os.makedirs(self.local_tmp_dir)

    def put_bin(self):
        self.run_ssh("rm -rf {}".format(self.bin_file))
        self.sftp.put(self.config.platon, self.node_dir)
        self.run_ssh('chmod +x {}'.format(self.bin_file))

    def put_nodekey(self):
        """
        upload nodekey
        :return:
        """
        nodekey_file = os.path.join(self.local_tmp_dir, "nodekey")
        with open(nodekey_file, 'w', encoding="utf-8") as f:
            f.write(self.node_key)
        self.run_ssh('mkdir -p {}'.format(self.data_dir))
        self.sftp.put(nodekey_file, self.nodekey_file)

    def put_blskey(self):
        """
        upload blskey
        :return:
        """
        blskey_file = os.path.join(self.local_tmp_dir, "blskey")
        with open(blskey_file, 'w', encoding="utf-8") as f:
            f.write(self.bls_prikey)
        self.run_ssh('mkdir -p {}'.format(self.data_dir))
        self.sftp.put(blskey_file, self.blskey_file)

    def put_genesis(self, genesis_file):
        """
        upload genesis
        :param genesis_file:
        :return:
        """
        self.run_ssh("rm -rf {}".format(self.genesis_file))
        self.sftp.put(genesis_file, self.genesis_file)

    def put_static(self):
        """
        upload static
        :return:
        """
        self.sftp.put(config.TMP_STATIC_FILE, self.static_file)

    # def init(self):
    #     """
    #     Initialize
    #     :return:
    #     """
    #     cmd = rf'{self.bin_file} --datadir {self.data_dir} init {self.genesis_file}'
    #     result = self.run_ssh(cmd)
    #     self.run_ssh("ls {}".format(self.data_dir))
    #     if len(result) > 0:
    #         raise Exception(rf'node {self.node_site} init failed: {result[0]}')
    #     logger.info(f'node-{self.node_site} init success')
    #
    # @_try_do
    # def clean(self):
    #     """
    #     clear node data
    #     :return:
    #     """
    #     self.stop()
    #     self.run_ssh("sudo -S -p '' rm -rf {};mkdir -p {}".format(self.node_dir, self.node_dir), self.password)
    #     self.run_ssh("ls {}".format(self.node_dir))
    #
    # @_try_do
    # def clean_db(self):
    #     """
    #     clear the node database
    #     :return:
    #     """
    #     self.stop()
    #     self.run_ssh("sudo -S -p '' rm -rf {}".format(self.db_dir), self.password)
    #
    # def clean_log(self):
    #     """
    #     clear node log
    #     :return:
    #     """
    #     self.stop()
    #     self.run_ssh(f'rm -rf {self.log_dir}; mkdir -p {self.log_dir}')
    #
    # @_try_do
    # def stop(self):
    #     """
    #     close node
    #     :return:
    #     """
    #     logger.info("Stop node:{}".format(self.node_site))
    #     self.__is_connected = False
    #     self.__is_ws_connected = False
    #     if not self.running:
    #         return True, "{}-node is not running".format(self.node_site)
    #     self.run_ssh("sudo -S -p '' supervisorctl stop {}".format(self.node_name), self.password)
    #
    # @_try_do
    # def start(self):
    #     """
    #     boot node
    #     :param is_init:
    #     :return:
    #     """
    #     is_success = self.stop()
    #     if not is_success:
    #         raise Exception("Stop failed")
    #     if is_init:
    #         self.init()
    #     self.append_log_file()
    #     result = self.run_ssh("sudo -S -p '' supervisorctl start " + self.node_name, self.password)
    #     for r in result:
    #         if "ERROR" in r or "Command 'supervisorctl' not found" in r:
    #             raise Exception("Start failed:{}".format(r.strip("\n")))
    #
    # @_try_do
    # def restart(self):
    #     """
    #     restart node
    #     :return:
    #     """
    #     self.append_log_file()
    #     result = self.run_ssh("sudo -S -p '' supervisorctl restart " + self.node_name, self.password)
    #     for r in result:
    #         if "ERROR" in r:
    #             raise Exception("restart failed:{}".format(r.strip("\n")))
    #
    # @_try_do
    # def update(self):
    #     """
    #     update node
    #     :return:
    #     """
    #
    #     def __update():
    #         # todo fix me
    #         self.stop()
    #         self.put_bin()
    #         self.start()
    #
    #     return self.try_do_resturn(__update)
    #
    # def close(self):
    #     """
    #     Close the node, delete the node data,
    #     delete the node supervisor configuration
    #     :return:
    #     """
    #     is_success = True
    #     msg = "close success"
    #     try:
    #         self.clean()
    #         self.run_ssh("sudo -S -p '' rm -rf /etc/supervisor/conf.d/{}.conf".format(self.node_name), self.password)
    #     except Exception as e:
    #         is_success = False
    #         msg = "{}-close failed:{}".format(self.node_site, e)
    #     finally:
    #         self.t.close()
    #         return is_success, msg
    #

    #
    # def create_keystore(self, password="88888888"):
    #     """
    #     create a wallet
    #     :param password:
    #     :return:
    #     """
    #     cmd = "{} account new --datadir {}".format(self.bin_file, self.data_dir)
    #     stdin, stdout, _ = self.ssh.exec_command("source /etc/profile;%s" % cmd)
    #     stdin.write(str(password) + "\n")
    #     stdin.write(str(password) + "\n")
    #

    #
    # def put_config(self):
    #     """
    #     upload config
    #     :return:
    #     """
    #     self.run_ssh("rm -rf {}".format(self.config_file))
    #     self.sftp.put(config.TMP_CONFIG_FILE, self.config_file)
    #

    #
    # def put_deploy_conf(self):
    #     """
    #     upload node deployment supervisor configuration
    #     :return:
    #     """
    #     logger.debug("{}-generate supervisor deploy conf...".format(self.node_site))
    #     supervisor_tmp_file = os.path.join(self.local_tmp_dir, "{}.conf".format(self.node_name))
    #     self.__gen_deploy_conf(supervisor_tmp_file)
    #     logger.debug("{}-upload supervisor deploy conf...".format(self.node_site))
    #     self.run_ssh("rm -rf {}".format(self.supervisor_file))
    #     self.run_ssh("mkdir -p {}".format(config.REMOTE_SUPERVISOR_TMP_DIR))
    #     self.sftp.put(supervisor_tmp_file, self.supervisor_file)
    #     self.run_ssh("sudo -S -p '' cp {} /etc/supervisor/conf.d".format(self.supervisor_file), self.password)
    #
    # def upload_file(self, local_file, remote_file):
    #     if local_file and os.path.exists(local_file):
    #         self.sftp.put(local_file, remote_file)
    #     else:
    #         logger.info("file: {} not found".format(local_file))
    #
    # def __gen_deploy_conf(self, sup_tmp_file):
    #     """
    #     Generate a supervisor configuration for node deployment
    #     :param sup_tmp_file:
    #     :return:
    #     """
    #     with open(sup_tmp_file, "w") as fp:
    #         fp.write("[program:" + self.node_name + "]\n")
    #         go_fail_point = ""
    #         if self.fail_point:
    #             go_fail_point = " GO_FAILPOINTS='{}' ".format(self.fail_point)
    #         cmd = "{} --identity platon --datadir".format(self.bin_file)
    #         cmd = cmd + " {} --port ".format(self.data_dir) + self.p2p_port
    #         cmd = cmd + " --db.nogc"
    #         cmd = cmd + " --nodekey " + self.nodekey_file
    #         cmd = cmd + " --cbft.blskey " + self.blskey_file
    #         cmd = cmd + " --config " + self.config_file
    #         cmd = cmd + " --syncmode '{}'".format(config.SYNC_MODE)
    #         cmd = cmd + " --debug --verbosity {}".format(config.NODE_LOG_LEVEL)
    #         if self.pprof_port:
    #             cmd = cmd + " --pprof --pprofaddr 0.0.0.0 --pprofport " + str(self.pprof_port)
    #         if self.ws_port:
    #             cmd = cmd + " --ws --wsorigins '*' --wsaddr 0.0.0.0 --wsport " + str(self.ws_port)
    #             cmd = cmd + " --wsapi platon,debug,personal,admin,net,web3"
    #         cmd = cmd + " --rpc --rpcaddr 0.0.0.0 --rpcport " + str(self.rpc_port)
    #         cmd = cmd + " --rpcapi platon,debug,personal,admin,net,web3,txpool"
    #         cmd = cmd + " --txpool.nolocals"
    #         if config.EXTRA_CMD:
    #             cmd = cmd + " " + config.EXTRA_CMD
    #         fp.write("command=" + cmd + "\n")
    #         if go_fail_point:
    #             fp.write("environment={}\n".format(go_fail_point))
    #         supervisor_default_conf = "numprocs=1\n" + "autostart=false\n" + "startsecs=1\n" + "startretries=3\n" + \
    #                                   "autorestart=unexpected\n" + "exitcode=0\n" + "stopsignal=TERM\n" + \
    #                                   "stopwaitsecs=10\n" + "redirect_stderr=self.password\n" + \
    #                                   "stdout_logfile_maxbytes=200MB\n" + "stdout_logfile_backups=20\n"
    #         fp.write(supervisor_default_conf)
    #         fp.write("stdout_logfile={}/platon.log\n".format(self.log_dir))
    #
    # def deploy(self, genesis_file) -> tuple:
    #     """
    #     deploy this node
    #     1. Empty environmental data
    #     2. According to the node server to determine whether it is necessary to upload files
    #     3. Determine whether to initialize, choose to upload genesis
    #     4. Upload the node key file
    #     5. Upload the inter-node supervisor configuration
    #     6. Start the node
    #     :param genesis_file:
    #     :return:
    #     """
    #     logger.debug("{}-clean node path...".format(self.node_site))
    #     is_success, msg = self.clean()
    #     if not is_success:
    #         return is_success, msg
    #     self.clean_log()
    #     is_success, msg = self.upload_files(genesis_file)
    #     if not is_success:
    #         return is_success, msg
    #     return self.start(self.cfg.init_chain)
    #
    # @_try_do
    # def upload_files(self, genesis_file):
    #     """ upload or copy the base file
    #     """
    #     ls = self.run_ssh(f'cd {config.REMOTE_RESOURCE_TMP_DIR}; ls')
    #     if self.cfg.res_id and (self.cfg.res_id + ".tar.gz\n") in ls:
    #         logger.debug("{}-copy bin...".format(self.node_dir))
    #         cmd = "cp -r {}/{}/* {}".format(config.REMOTE_RESOURCE_TMP_DIR, self.cfg.res_id,
    #                                         self.node_dir)
    #         self.run_ssh(cmd)
    #         self.run_ssh("chmod +x {};mkdir {}".format(self.bin_file, self.log_dir))
    #     else:
    #         self.put_bin()
    #         self.put_config()
    #         # self.put_static()
    #         self.create_keystore()
    #     if self.cfg.init_chain:
    #         logger.debug("{}-upload genesis...".format(self.node_site))
    #         self.put_genesis(genesis_file)
    #     if self.cfg.is_need_static:
    #         self.put_static()
    #     logger.debug("{}-upload blskey...".format(self.node_site))
    #     self.put_blskey()
    #     logger.debug("{}-upload nodekey...".format(self.node_site))
    #     self.put_nodekey()
    #     self.put_deploy_conf()
    #     self.run_ssh("sudo -S -p '' supervisorctl update " + self.node_name, self.password)
    #
    # @_try_do
    # def download_log(self):
    #     """
    #     download log
    #     :return:
    #     """
    #     self.run_ssh("cd {};tar zcvf log.tar.gz ./log".format(self.node_dir))
    #     self.sftp.get("{}/log.tar.gz".format(self.node_dir),
    #                   "{}/{}_{}.tar.gz".format(self.cfg.tmp_log, self.host, self.p2p_port))
    #     self.run_ssh("cd {};rm -rf ./log.tar.gz".format(self.node_dir))
