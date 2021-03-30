import os
from functools import wraps
from loguru import logger
from config import Config, NodeInfo as NodeInfo
from host import Host


failed_msg = r'Node {} do {} failed:{}'
success_msg = r'Node {} do {} success'


def _try_do(func, *args, **kwargs):
    @wraps(func)
    def wrap_func(self, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            return False, failed_msg.format(self.host, func.__name__, e)
        return True, success_msg.format(self.host, func.__name__)
    return wrap_func


class Node(Host):
    def __init__(self, node_info: NodeInfo, config: Config):
        super().__init__(node_info, config)
        self.p2p_port = node_info.p2p_port
        self.rpc_port = node_info.rpc_port
        self.ws_port = node_info.ws_port
        self.node_id = node_info.node_id
        self.node_key = node_info.node_key
        self.bls_pubkey = node_info.bls_pubkey
        self.bls_prikey = node_info.bls_prikey
        self.node_make = f'{self.host}:{self.p2p_port}'
        self.node_name = f'p{self.p2p_port}'
        # remote deploy info
        if not os.path.isabs(self.config.deploy_dir):
            self.config.deploy_dir = os.path.join(self._pwd, self.config.deploy_dir)
        self.node_dir = os.path.join(self.config.deploy_dir, self.node_name)

    @property
    def enode(self):
        return f'enode://{self.node_id}@{self.host}:{self.p2p_port}'

    @property
    def running(self) -> bool:
        return bool(self.run_ssh(f"ps -ef|grep platon|grep port|grep {self.p2p_port}|grep -v grep|awk {'print $2'}"))

    def create_keystore(self, password):
        """ create a wallet
        """
        cmd = "{} account new --datadir {}".format(self.bin_file, self.data_dir)
        stdin, stdout, _ = self.ssh.exec_command("source /etc/profile;%s" % cmd)
        stdin.write(str(password) + "\n")
        stdin.write(str(password) + "\n")

    def init(self):
        """ Initialize
        """
        cmd = rf'{self.bin_file} --datadir {self.data_dir} init {self.genesis_file}'
        result = self.run_ssh(cmd)
        self.run_ssh("ls {}".format(self.data_dir))
        if len(result) > 0:
            raise Exception(rf'node {self.node_make} init failed: {result[0]}')
        logger.info(f'node-{self.node_make} init success')

    def deploy(self) -> tuple:
        self.clean()
        self._upload_files()
        self.init()
        self.start()

    def start(self):
        is_success = self.stop()
        if not is_success:
            raise Exception("Stop failed")
        if is_init:
            self.init()
        self.append_log_file()
        result = self.run_ssh("sudo -S -p '' supervisorctl start " + self.node_name, self.password)
        for r in result:
            if "ERROR" in r or "Command 'supervisorctl' not found" in r:
                raise Exception("Start failed:{}".format(r.strip("\n")))

    def stop(self):
        if not self.running:
            return True, f"node {self.node_make} node is not running"
        self.run_ssh("sudo -S -p '' supervisorctl stop {}".format(self.node_name), self.password)

    def restart(self):
        result = self.run_ssh("sudo -S -p '' supervisorctl restart " + self.node_name, self.password)
        for r in result:
            if "ERROR" in r:
                raise Exception("restart failed:{}".format(r.strip("\n")))

    @_try_do
    def update(self):
        # 更新Platon并重启
        # todo: coding
        self.restart()

    def clean(self):
        self.stop()
        self.run_ssh(f"sudo -S -p '' rm -rf {self.node_dir}", self.password)

    def clean_db(self):
        """ clear the node database
        """
        self.stop()
        self.run_ssh("sudo -S -p '' rm -rf {}".format(self.db_dir), self.password)

    def clean_log(self):
        """ clear node log
        """
        self.stop()
        self.run_ssh(f'rm -rf {self.log_dir}; mkdir -p {self.log_dir}')

    def shutdown(self):
        """ Close the node, delete the node data, delete the node supervisor configuration
        """
        is_success = True
        msg = "close success"
        try:
            self.remove()
            self.run_ssh("sudo -S -p '' rm -rf /etc/supervisor/conf.d/{}.conf".format(self.node_name), self.password)
        except Exception as e:
            is_success = False
            msg = "{}-close failed:{}".format(self.node_make, e)
        finally:
            self.t.close()
            return is_success, msg

    def _upload_files(self, genesis_file):
        """ upload or copy the base file
        """
        ls = self.run_ssh(f'cd {config.REMOTE_RESOURCE_TMP_DIR}; ls')
        if self.cfg.res_id and (self.cfg.res_id + ".tar.gz\n") in ls:
            logger.debug("{}-copy bin...".format(self.node_dir))
            cmd = "cp -r {}/{}/* {}".format(config.REMOTE_RESOURCE_TMP_DIR, self.cfg.res_id,
                                            self.node_dir)
            self.run_ssh(cmd)
            self.run_ssh("chmod +x {};mkdir {}".format(self.bin_file, self.log_dir))
        else:
            self._upload_platon()
            self._upload_config()
            # self.put_static()
            self.create_keystore()
        if self.cfg.init_chain:
            logger.debug("{}-upload genesis...".format(self.node_make))
            self._upload_genesis(genesis_file)
        if self.cfg.is_need_static:
            self._upload_static()
        logger.debug("{}-upload blskey...".format(self.node_make))
        self._upload_blskey()
        logger.debug("{}-upload nodekey...".format(self.node_make))
        self._upload_nodekey()
        self._put_supervisorctl_cfg()
        self.run_ssh("sudo -S -p '' supervisorctl update " + self.node_name, self.password)

    def _upload_platon(self):
        # todo: 从缓存获取platon
        self.run_ssh("rm -rf {}".format(self.bin_file))
        self.sftp.put(self.config.platon, self.node_dir)
        self.run_ssh('chmod +x {}'.format(self.bin_file))

    def _upload_nodekey(self):
        """ upload nodekey
        """
        nodekey_file = os.path.join(self.local_tmp_dir, "nodekey")
        with open(nodekey_file, 'w', encoding="utf-8") as f:
            f.write(self.node_key)
        self.run_ssh('mkdir -p {}'.format(self.data_dir))
        self.sftp.put(nodekey_file, self.nodekey_file)

    def _upload_blskey(self):
        """ upload blskey
        """
        blskey_file = os.path.join(self.local_tmp_dir, "blskey")
        with open(blskey_file, 'w', encoding="utf-8") as f:
            f.write(self.bls_prikey)
        self.run_ssh('mkdir -p {}'.format(self.data_dir))
        self.sftp.put(blskey_file, self.blskey_file)

    def _upload_static(self):
        """ upload static
        """
        self.sftp.put(config.TMP_STATIC_FILE, self.static_file)

    def _upload_genesis(self, genesis_file):
        """ upload genesis
        """
        self.run_ssh("rm -rf {}".format(self.genesis_file))
        self.sftp.put(genesis_file, self.genesis_file)

    def _upload_config(self):
        """ upload config
        """
        self.run_ssh("rm -rf {}".format(self.config_file))
        self.sftp.put(config.TMP_CONFIG_FILE, self.config_file)

    def _put_supervisorctl_cfg(self):
        """ upload node deployment supervisor configuration
        """
        logger.debug("{}-generate supervisor deploy conf...".format(self.node_make))
        supervisor_tmp_file = os.path.join(self.local_tmp_dir, "{}.conf".format(self.node_name))
        self._gen_supervisorctl_cfg(supervisor_tmp_file)
        logger.debug("{}-upload supervisor deploy conf...".format(self.node_make))
        self.run_ssh("rm -rf {}".format(self.supervisor_file))
        self.run_ssh("mkdir -p {}".format(config.REMOTE_SUPERVISOR_TMP_DIR))
        self.sftp.put(supervisor_tmp_file, self.supervisor_file)
        self.run_ssh("sudo -S -p '' cp {} /etc/supervisor/conf.d".format(self.supervisor_file), self.password)

    def _gen_supervisorctl_cfg(self, sup_tmp_file):
        """ Generate a supervisor configuration for node deployment
        """
        with open(sup_tmp_file, "w") as fp:
            fp.write("[program:" + self.node_name + "]\n")
            go_fail_point = ""
            if self.fail_point:
                go_fail_point = " GO_FAILPOINTS='{}' ".format(self.fail_point)
            cmd = "{} --identity platon --datadir".format(self.bin_file)
            cmd = cmd + " {} --port ".format(self.data_dir) + self.p2p_port
            cmd = cmd + " --db.nogc"
            cmd = cmd + " --nodekey " + self.nodekey_file
            cmd = cmd + " --cbft.blskey " + self.blskey_file
            cmd = cmd + " --config " + self.config_file
            cmd = cmd + " --syncmode '{}'".format(config.SYNC_MODE)
            cmd = cmd + " --debug --verbosity {}".format(config.NODE_LOG_LEVEL)
            if self.pprof_port:
                cmd = cmd + " --pprof --pprofaddr 0.0.0.0 --pprofport " + str(self.pprof_port)
            if self.ws_port:
                cmd = cmd + " --ws --wsorigins '*' --wsaddr 0.0.0.0 --wsport " + str(self.ws_port)
                cmd = cmd + " --wsapi platon,debug,personal,admin,net,web3"
            cmd = cmd + " --rpc --rpcaddr 0.0.0.0 --rpcport " + str(self.rpc_port)
            cmd = cmd + " --rpcapi platon,debug,personal,admin,net,web3,txpool"
            cmd = cmd + " --txpool.nolocals"
            if config.EXTRA_CMD:
                cmd = cmd + " " + config.EXTRA_CMD
            fp.write("command=" + cmd + "\n")
            if go_fail_point:
                fp.write("environment={}\n".format(go_fail_point))
            supervisor_default_conf = "numprocs=1\n" + "autostart=false\n" + "startsecs=1\n" + "startretries=3\n" + \
                                      "autorestart=unexpected\n" + "exitcode=0\n" + "stopsignal=TERM\n" + \
                                      "stopwaitsecs=10\n" + "redirect_stderr=self.password\n" + \
                                      "stdout_logfile_maxbytes=200MB\n" + "stdout_logfile_backups=20\n"
            fp.write(supervisor_default_conf)
            fp.write("stdout_logfile={}/platon.log\n".format(self.log_dir))


