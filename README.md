# PlatON-Deploy
PlatON 区块链网络部署工具

### 字段详解

```yml
consensus: # 共识节点，有时必填
- host: 10.10.8.236 # 节点ip，必填
  username: juzhen  # 节点机器账户，必填
  password: Platon123! # 节点机器密码，必填
  id: 5b068ef1cfeef626d9ad131d08b889002a2f5c7306ff34c3032ad04fcc92fd234d0c7272014068eb998dae2abfe9f10271ed6731963b1cf22ec944abd8fb0f9e # 节点公钥，非必填，最好不填
  nodekey: 3314532da43158885d8db07e0b25dc0c194c8382c4fa5ce8c28a0b7c86cdec16 # 节点私钥，非必填，最好不填，需要与公钥对应
  blspubkey: e3797fad1041ecbd0b91b444de1f063ab74849a0fffa9fa9565ca2b0f78a1420a036d529be9f81576bcb836653436ac0e6eb91143b2e04cb1b0dc93da3ddf893 # bls公钥，必填
  blsprikey: e4c7bb7918e474bff76b07361ec44b2d613fb9cfb58a296a90bcfbf7bace491f # bls私钥，必填
  port: 16789 # p2p端口，非必填，最好填
  rpcport: 6789 # rpc端口，非必填，最好填
  url: http://10.10.8.236:6789 # rpc url，非必填，最好不填
  wsport: 6790 # ws端口，非必填，填了才会开ws
  wsurl: ws://10.10.8.236:6790 # ws url，非必填，与wsport匹配，最好不填
- host: 10.10.8.237
  username: 
  password: 
  id: 
  nodekey: 
  port: 
  rpcport: 
  url: 
noconsensus: # 非共识节点，有时必填
- host: 10.10.8.239
  username: 
  password: 
  protocol: 
  id: 
  nodekey: 
  port: 
  rpcport: 
  url: 
  ```


### 配置文件模版

```yml




  ```