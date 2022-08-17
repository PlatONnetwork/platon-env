# platon-env
PlatON区块链部署工具，能够帮你自由的部链、加入、管理PlatON区块链


## 安装方法
```shell
pip install platon_env
```


## 使用方法
```python
from platon_env.chain import Chain

# 按照配置文件内容，部署区块链
chain_file = 'env-files/chain_file.yml'
chain = Chain.from_file(chain_file)
chain.install()
```


## 配置文件

```yml
chain:
  platon: env-files/bin/platon  # platon二进制
  network: private  # 网络形式，支持private、public，为private时必须指定genesis
  genesis: env-files/genesis.json  # 创世文件
  keystore: env-files/keystore  # 要上传到节点的钱包文件，支持文件或目录形式（每个节点都会上传）
  ssl: false  # 使用基于https、wss使用rlp
  deploy_dir: chain  # 节点要部署到远程主机的哪个路径
  init:
    # 节点公共信息，每个节点可以单独指定
    username: platon
    password: Platon123!
    ssh_port: 22
    p2p_port: 16789
    options: '--graphql --http --http.addr 0.0.0.0 --http.port 6789 --http.api web3,platon,txpool,net,admin,personal,debug --http.ethcompatible --ws --ws.addr 0.0.0.0 --ws.port 6790 --wsapi web3,platon,txpool,net,admin,personal,debug --ws.origins "*" --allow-insecure-unlock --txpool.nolocals --nodiscover --db.nogc --debug --verbosity 5'
    nodes:
      - host: 192.168.120.121
        node_id: 18e5d83b36e1959206b5e582053ae994a00731ccbd7d7ddb6ac7d07eab6ee1d859af91784da6d05336ae04cd96bfc0ae7732818fb2c7ac10e4986a591258239d
        node_key: 193181eeed7d209726f4f2302957b1d1f4f358f563a466a25aa44653bc2a3f2e
        bls_pubkey: d2c26ea474e89da808adc9cc3b8c857c1c5457e607b6f138dbe2f4f180613bcdcb533301e3de497a92f922ae99cd390f23e2872c95319a8d7ff40dc1b72cb568774df227a6543e9fec37c77d9032e9206f3ac8e219f5a71779a1d54779f85393
        bls_prikey: b5791a67118556a322c3609ea0cc21b9d1d51d1755104c130ab9a4d0c6b6b336
      - host: 192.168.120.122
        node_id: 94098f49eb8a8e4b2d37e693677c0777ee2b0bad072e46cc506f51c058f3737ea8d41e723ff9c34d9677c1abdde1dbb30780fa69b752148165228ef2f82194c2
        node_key: 936309fded6a2fff7401905eb09eece224a23dc944191f981f9d608961f367da
        bls_pubkey: e6e593cfa009a85ab91683a26e701f1c68e460ce0e25284d5e22949f39800d1bd5e21c8604c538f0db0bd3bc79d22d0a25bcc3ba8927a8a3cd05ba045fc3e52bb061b53ac45968830e248d7fa18ca3d9b452bf0c1690411a0304aa55fe139d89
        bls_prikey: b728d85bdf2c935b5718f42cf7492aef98098476b6dc796da082ab73969ccf05
      - host: 192.168.120.123
        node_id: 3e85fbbc561d91ddb7a8b263a65508040a1c5d6e79f2fb823a32dfb011b578e913522587be2a1f8ac2a86900daa6b0ce3aac43a388d1a900118a68047eedb8ba
        node_key: 4bb99dd4b3d64cd1719c30cda95a4ff3b07503bbbf0c7d83f3dda10f1e589356
        bls_pubkey: e00fba1c3388382505753ab53a37efa411877fabdd7a33481f9c9edce033c67d5f5487a637499c90ba147f95d51266003409b14ed4dbf07f923c093f60ae9f5c02447c136e47290ffbf9490f3a2e06f354d3f0ee88719773ed97b857032f9905
        bls_prikey: 0df00258db84cdac012a6e2b2d70c96c78474c3b4c8558eedd87f03b08fbd462
      - host: 192.168.120.124
        node_id: 4b9015c94a2fea0c1f9472a6925a3ea2f951a606222ab231a31310e15d8c272545ee06e6895fc5ad384fc2cacde359ab452069643ef1fb7a4e87539a1a2283de
        node_key: 6d8cd70325e43ea12bf47fca53b4f4aaee9f36519bf1919c39e0deaa8d5713e7
        bls_pubkey: c2c67121901f37be5c56ed6e303a0ee11070b1447cfd09dcff283a5dc30dda729dcc4d96d26b49b8bd71de733db3440fc9cf9253bdc67ea8c8ed204d6d0784e60a38e416b3c5b56cf1e895dfff2fa07f98f1d0bc12f8186f68af9ee53c636d0b
        bls_prikey: 1ce1918e8561bae51d2cfd3edb03612f504461884e3253ee9bd4f684b1791e4b
  normal:
    # 节点公共信息，每个节点可以单独指定
    username: platon
    password: Platon123!
    ssh_port: 22
    p2p_port: 17789
    options: '--graphql --http --http.addr 0.0.0.0 --http.port 7789 --http.api web3,platon,txpool,net,admin,personal,debug --http.ethcompatible --ws --ws.addr 0.0.0.0 --ws.port 7790 --wsapi web3,platon,txpool,net,admin,personal,debug --ws.origins "*" --allow-insecure-unlock --txpool.nolocals --nodiscover --db.nogc --debug --verbosity 5'
    nodes:
      - host: 192.168.120.121
        node_id: d5cce29d07a066eae8fe4a34049cbd2d68d92bf02bc618ae2d43f0b355ad1678c2e447ae3fcf18296f8c4434d83de3546854b166f379c250a6cb10702383407e
        node_key: a0f2d594e24be366889207a9379d46a0080fde197f2211b71bfcee8883a1daff
        bls_pubkey: 3b73fdfa4af6fb84873c06ad89eda5de72d3b8f0f8572d2a85479afcf4d6889e9da127dc6dea597ad83abf8ed61484097496cdf1cd6712e453caef2c6ceb06654b894e986f7d0bfd8ecda12f9345264f750f73d621d916becb5aaec1fbf78e0d
        bls_prikey: d168ab9a60dd97781d3ffd8e47cf897124d5b2a8c6d5d1f9c9859b8a646cb935
      - host: 192.168.120.122
        node_id: a5880c17478c173f407e38c997c4defe290779d15dda19a1e1bd5ca66429006cd7007fd8e1590df120f6f590c3aa054bbb29d0ab01b48a52ede6e4bd53c82c12
        node_key: d82486ddb342f3568d08644b23a85d5e83d72f76417a423e229a65e7828e10d2
        bls_pubkey: 64dec26c755c0b08f7e7e80b0e299cf273e2a8ee26540fa16ca9287c2d9a7076f6d9971bf5974b2b8e9e86858a27130f570a682dcd12074a35051d8a1ab86934efbddffa1e9c110851447c0ea849d90bd808d9f683786fbbfb184fc7dba4aa13
        bls_prikey: 5928f389e6f102719b69c5dae5573eb20bd3abdfa9e347a9e4382f8f3cbd2839
      - host: 192.168.120.123
        node_id: 230d7bf50fdfb4009b51fe31c1387a74d6df7caabcd4b64aa609e9071292a5cce0bfbe9e9ff33bdd7da5d05604d395ecf5046425d2eb20cca880eaae3359e224
        node_key: 8ed2bdfb2c6766db4b5505c54b7b56c862408cb86bc876ab89c826f825c60b15
        bls_pubkey: 34f14b10ae3d107678d118a4a6370efde95d7162ed07f0538e6442d6b82921bba5513b37952525aad86b97604be15e0d5cf6d35ea9b09843e441f011f7852de244e20017a64db4e8b4e0afa18add690fed09cba5e8fa4b928a22d90c1cd15597
        bls_prikey: 1c8545964a63699267dd8c76e7f8e7134dd18db7ee8ed830a359a584cbb3bb35
      - host: 192.168.120.124
        node_id: 94be7422fec178f07cc1071d2de8b856dbb082518143b91b7a22467944a2d9ef78fd3559fb73437069a908a0042f7613fe73bb4fc80c11a76c35b43eed2079c2
        node_key: 2d4472a210ce437181b0332cf25863cea597348ec4170d91978b7ddcbc185085
        bls_pubkey: ab0f251830934d41eff50b811c8c056c0ff5ae60d4e1f12a76a0c429c50d76ca7c26ca698fec5eab3706cd5998b78d0d2c4cf45cb4ea9255229951fc8ea442d815c916c403ba877f396c2579d80812eb5f074d62d6bf749070ade651fc51db05
        bls_prikey: d5e8a21ad50d87284a3001747b093f768d4b6d3696418a5268288be221262420
  ```

