This documentation explains how to set up a multi-node BigChainDB network using Docker in a test environment and run the proposed visual demo.  
Please note, this setup is **not intended for production use**, but it provides a solid foundation to understand distributing BigChainDB components across multiple nodes.


## Overview

In this setup, we use the **`bigchaindb:all-in-one`** Docker image, which conveniently runs:

- **MongoDB** (database)
- **Tendermint** (consensus engine)
- **BigchainDB server**

While suitable for testing, in production, each component should ideally run on dedicated machines or containers with specific configurations for scalability and security.

## Creating the Docker Network 🌊

To allow all nodes to communicate seamlessly, create a dedicated Docker network:

```javascript
docker network create bigchaindb-net
```

Download the latest `all-in-one` image:

```javascript
docker pull bigchaindb/bigchaindb:all-in-one
```

## Preparing Storage Directories 💾

In a production-like environment, persistent data storage is crucial. For each node, create directories for MongoDB data and Tendermint configuration:

```javascript
# For node 1
mkdir -p $HOME/BigChainDBDemo/bigchainDB1/mongodb/data/db
mkdir -p $HOME/BigChainDBDemo/bigchainDB1/mongodb/data/configdb
mkdir -p $HOME/BigChainDBDemo/bigchainDB1/tendermint

# For node 2
mkdir -p $HOME/BigChainDBDemo/bigchainDB2/mongodb/data/db
mkdir -p $HOME/BigChainDBDemo/bigchainDB2/mongodb/data/configdb
mkdir -p $HOME/BigChainDBDemo/bigchainDB2/tendermint

# Continue similarly for additional nodes...
```

Set proper permissions so Docker containers can write to these directories:

```javascript
sudo chcon -Rt container_file_t $HOME/BigChainDBDemo/
```

_Note:_ This command is Linux-specific and may vary based on your system.

## Launching the Coordinator and Member Nodes 🚀

Now, launch each node by running separate containers, mapping the ports and volumes appropriately.
#### Example for Node 1 (coordinator1):

```javascript
docker run -d \
  --name=coordinator1 \
  --network=bigchaindb-net \
  --publish=9984:9984 \
  --publish=9985:9985 \
  --publish=26657:26657 \
  --volume=$HOME/BigChainDBDemo/bigchainDB1/mongodb/data/db:/data/db \
  --volume=$HOME/BigChainDBDemo/bigchainDB1/mongodb/data/configdb:/data/configdb \
  --volume=$HOME/BigChainDBDemo/bigchainDB1/tendermint:/tendermint \
  bigchaindb/bigchaindb:all-in-one
```

Similarly, for other nodes, change container names, port mappings, and volume paths:

|Node Name|Host Ports (MongoDB)|Tendermint Ports|Volume Paths|
|---|---|---|---|
|member2|9986:9984, 9987:9985|26658:26657|`$HOME/BigChainDBDemo/bigchainDB2/...`|
|member3|9988:9984, 9989:9985|26659:26657|`$HOME/BigChainDBDemo/bigchainDB3/...`|
|member4|9990:9984, 9991:9985|26660:26657|`$HOME/BigChainDBDemo/bigchainDB4/...`|

**Note**: Adjust the port mappings to avoid conflicts.


Here's a quick reference for the port configurations for each node for this example:

| Node         | MongoDB Port (Host:Container) | Tendermint Port (Host:Container) |
| ------------ | ----------------------------- | -------------------------------- |
| coordinator1 | 9984:9984                     | 26657:26657                      |
| member2      | 9986:9984                     | 26658:26657                      |
| member3      | 9988:9984                     | 26659:26657                      |
| member4      | 9990:9984                     | 26660:26657                      |

**What is the Coordinator Node?**

the _Coordinator_ plays a **central role in orchestrating network operations**:
- **Initiates the network**, acting as the primary node responsible for setup.
- **Creates the initial genesis block and configuration files** (like `genesis.json`), which are **distributed to other nodes**.
- **Manages cluster-wide settings**, including peer connections, node identities, and consensus parameters.
- **Serves as the entry point** for network management tasks such as adding new nodes, updating configurations, or troubleshooting.

for further information, consult the bigchaindb official documentation: 
https://docs.bigchaindb.com/projects/server/en/latest/simple-deployment-template/network-setup.html

## Testing Endpoints 🔧

Verify your nodes are running correctly:

- **BigchainDB server:**

```javascript
curl http://localhost:9984/
```

- **Tendermint status:**


```javascript
curl http://localhost:26657/status/
```

- **Peers info:**

```javascript
curl http://localhost:26657/net_info
```

## Inspecting Container Configurations 🔍

To see what directories are mounted:

Copy code

```javascript
docker inspect coordinator1 | grep -A 10 "Mounts"
```

This helps confirm the correct volume mappings and identify config file locations.
## Enter in a container

if you want to enter in a container, use:

`docker exec -it coordinator1 /bin/bash`


## Managing Configuration Files & Parameters 📂

`genesis.json` is the **initial configuration file or the "genesis block"** for your Tendermint blockchain network. It contains important network parameters, validator info, and consensus settings like:

- Chain ID
- Validators' public keys
- Initial state (e.g., accounts, balances)
- Network settings

This file must be **identical on all nodes** to ensure they together form a consistent blockchain.

### How to Share and Distribute the `genesis.json`

- Copy the `genesis.json` **to all nodes' Tendermint config folders**.

let's start extracting genesis.json from coordinator1 node

```javascript
docker cp coordinator1:/tendermint/config/genesis.json .
```

``` json
{
   "genesis_time":"2025-11-16T23:37:54.466847445Z",
   "chain_id":"test-chain-274NpV",
   "consensus_params":{
      "block_size_params":{
         "max_bytes":"22020096",
         "max_txs":"10000",
         "max_gas":"-1"
      },
      "tx_size_params":{
         "max_bytes":"10240",
         "max_gas":"-1"
      },
      "block_gossip_params":{
         "block_part_size_bytes":"65536"
      },
      "evidence_params":{
         "max_age":"100000"
      }
   },
   "validators":[
      {
         "pub_key":{
            "type":"tendermint/PubKeyEd25519",
            "value":"wfWpYJ1zbUoDeieMSdBSSLV3HEdnTKHeOZHCOvi9Z2E="
         },
         "power":"10",
         "name":""
      }
   ],
   "app_hash":""
}
```


for each node in the network we will have a validator with its pub_key (node name is optional)

we can find the pub_key of the others node in this tenderming configuration file:
/tendermint/config/priv_validator.json

so since we are using a persistent tenderming for each node, we can extract the key in this way instad of entering in each container

```bash 
 cat $HOME/BigChainDBDemo/bigchainDB2/tendermint/config/priv_validator.json 
```

```bash 
{
  "address": "5BD0D502C02BB9A3013BD79E1CE0256A5A326FAF",
  "pub_key": {
    "type": "tendermint/PubKeyEd25519",
    "value": "PAK1enS0Hkv38feNbVhYNInZJ80fXd03xwcu0yL5vbE="
  },

```
and so on for other node


we will copy the modified genesis.json file in each tendermint folder


cp genesis.json $HOME/BigChainDBDemo/bigchainDB1/tendermint/config/

and so on for other nodes

## `config.toml`

`config.toml` is the primary configuration file for **Tendermint** that determines how your node operates within the blockchain network. It contains settings related to network connectivity, consensus, logging, and other operational parameters.

``` 
docker cp coordinator1:/tendermint/config/config.toml .
```


## Main parameters to set

Example snippet:

Copy code

```javascript
moniker             = "Coordinator"
log_level           = "main:info,state:info,*:error"
persistent_peers    = "a29acdfc2953220183538296a530601502326856@hostname:26656"
addr_book_strict    = false
send_rate           = 102400000
recv_rate           = 102400000
create_empty_blocks = false
```

Short explanation:

- `moniker`
    
    - Human‑readable node name (any string you like).
    - Example: `"Coordinator"`, `"node1"`, `"validator-eu"`.
- `log_level`
    
    - Logging level; usually you can keep:
        - `"main:info,state:info,*:error"`.
- `persistent_peers`
    
    - Peers this node should always connect to.
    - Format: `"NODE_ID@hostname:26656,NODE_ID2@hostname2:26656"`
    - `NODE_ID` = Tendermint node ID of the other node.
- `addr_book_strict`
    
    - If using private IPs, set to `false`.
    - Example: `addr_book_strict = false`.
- `send_rate`
    
    - Max bytes per second this node can send.
    - From your doc: `send_rate = 102400000`.
- `recv_rate`
    
    - Max bytes per second this node can receive.
    - From your doc: `recv_rate = 102400000`.
- `create_empty_blocks`
    
    - Whether to create blocks even with no transactions.
    - From your doc: set to `false`:
        - `create_empty_blocks = false`.

## How to get the node ID (for `persistent_peers`) 

Enter a container: and On each node, run:

Copy code

```javascript
tendermint show_node_id
```

Then build the peer string:

Copy code

```javascript
NODE_ID@hostname:26656
```

>the port is the 2556 for all the nodes


Example:

Copy code

```javascript
a29acdfc2953220183538296a530601502326856@my-node.example.com:26656
```

Use this string inside `persistent_peers` on the other nodes.


example

coordinator1 e535544d3e733013787fc0a73670962c31c83dfb
member2 b2fdaca05c6a2859008bea5a2089a344f232c4e7
member3 00bc55e366f2247b71e3d903b1fb5286c2f63015
member4 ee08d1331bdb3916d93e3d6eb91ab76b52b8650b

## 4. Getting the IPs of the containers

```javascript
docker network inspect bigchaindb-net
```

``` 
 docker network inspect bigchaindb-net
Emulate Docker CLI using podman. Create /etc/containers/nodocker to quiet msg.
[
     {
          "name": "bigchaindb-net",
          "id": "5eb9c3c0f33d9de6b868052a7f71bc317d25fa08d2306d91897798dd74e6eee0",
          "driver": "bridge",
          "network_interface": "podman1",
          "created": "2025-11-16T20:58:38.587432589+01:00",
          "subnets": [
               {
                    "subnet": "10.89.0.0/24",
                    "gateway": "10.89.0.1"
               }
          ],
          "ipv6_enabled": false,
          "internal": false,
          "dns_enabled": true,
          "ipam_options": {
               "driver": "host-local"
          },
          "containers": {
               "05a7f297554bac7499df06a0b021f3d188cf651ed9e9693a29eef7e7f374ec01": {
                    "name": "member2",
                    "interfaces": {
                         "eth0": {
                              "subnets": [
                                   {
                                        "ipnet": "10.89.0.3/24",
                                        "gateway": "10.89.0.1"
                                   }
                              ],
                              "mac_address": "aa:f6:5b:fe:2e:28"
                         }
                    }
               },
               "164f4d25a6a4c8fb9798d5d6a5b8a7c78d36e7ca1b2cd818f917c3f7b7096350": {
                    "name": "coordinator1",
                    "interfaces": {
                         "eth0": {
                              "subnets": [
                                   {
                                        "ipnet": "10.89.0.2/24",
                                        "gateway": "10.89.0.1"
                                   }
                              ],
                              "mac_address": "82:2e:6f:4b:93:71"
                         }
                    }
               },
               "7380c0e1a6eaf52af89c119829faa6d058f671a1eb2d083d9677570df6e1dbd8": {
                    "name": "member3",
                    "interfaces": {
                         "eth0": {
                              "subnets": [
                                   {
                                        "ipnet": "10.89.0.4/24",
                                        "gateway": "10.89.0.1"
                                   }
                              ],
                              "mac_address": "1e:ce:86:c1:db:cc"
                         }
                    }
               },
               "fef90563330a2a7e583d2b850a487c0ccb895bf00908d38623d42a690b88b023": {
                    "name": "member4",
                    "interfaces": {
                         "eth0": {
                              "subnets": [
                                   {
                                        "ipnet": "10.89.0.5/24",
                                        "gateway": "10.89.0.1"
                                   }
                              ],
                              "mac_address": "4a:4b:f3:18:e6:f6"
                         }
                    }
               }
          }
     }
]
```

so we will have 

coordinator1 e535544d3e733013787fc0a73670962c31c83dfb 10.89.0.2:26656
member2 b2fdaca05c6a2859008bea5a2089a344f232c4e7 10.89.0.3:26656 
member3 00bc55e366f2247b71e3d903b1fb5286c2f63015 10.89.0.4:26656 
member4 ee08d1331bdb3916d93e3d6eb91ab76b52b8650b 10.89.0.5:26656

## Fast command to set node with seed

for node 1 we insert the others 3 
``` shell
PEERS="b2fdaca05c6a2859008bea5a2089a344f232c4e7@10.89.0.3:26656,00bc55e366f2247b71e3d903b1fb5286c2f63015@10.89.0.4:26656,ee08d1331bdb3916d93e3d6eb91ab76b52b8650b@10.89.0.5:26656"
sed -i 's/^persistent_peers = .*/persistent_peers = "'"$PEERS"'"/' /tendermint/config/config.toml
```

node 2 ...

``` shell
PEERS="e535544d3e733013787fc0a73670962c31c83dfb@10.89.0.2:26656,00bc55e366f2247b71e3d903b1fb5286c2f63015@10.89.0.4:26656,ee08d1331bdb3916d93e3d6eb91ab76b52b8650b@10.89.0.5:26656"
```

node 3


``` shell
PEERS="e535544d3e733013787fc0a73670962c31c83dfb@10.89.0.2:26656,e535544d3e733013787fc0a73670962c31c83dfb@10.89.0.2:26656,ee08d1331bdb3916d93e3d6eb91ab76b52b8650b@10.89.0.5:26656"
```

node 4 

``` shell
PEERS="e535544d3e733013787fc0a73670962c31c83dfb@10.89.0.2:26656,e535544d3e733013787fc0a73670962c31c83dfb@10.89.0.2:26656,e535544d3e733013787fc0a73670962c31c83dfb@10.89.0.2:26656"
```



in each node we run separate this command so che we set also other parameter 

### config moniker

``` shell
sed -i 's/^moniker = .*/moniker = "Member4"/' /tendermint/config/config.toml
```

### log config

``` bash
sed -i 's/^log_level = .*/log_level = "main:info,state:info,*:error"/' /tendermint/config/config.toml
```

###  false

``` bash
sed -i 's/^addr_book_strict = .*/addr_book_strict = false/' /tendermint/config/config.toml
```

### send e recv rate

``` bash
sed -i 's/^send_rate = .*/send_rate = 102400000/' /tendermint/config/config.toml
```

``` shell
sed -i 's/^recv_rate = .*/recv_rate = 102400000/' /tendermint/config/config.toml
```

### creation empty block false

``` bash
echo "sed -i 's/^create_empty_blocks = .*/create_empty_blocks = false/' /tendermint/config/config.toml"
```


we want to restart everything on each node 

``` 
monit stop all
sleep 5

# 2. Reset completo di Tendermint
tendermint unsafe_reset_all
tendermint init

# 3. Verifica che il database MongoDB sia pulito(evitare problemi di hash)
mongo --eval "db.dropDatabase()" bigchain 

# 4. Reinizializza BigchainDB
bigchaindb init

# 5. Verifica i permessi
chmod -R 755 /tendermint
chown -R $(whoami):$(whoami) /tendermint

# 6. Riavvia i servizi nell'ordine corretto
monit start mongodb
sleep 10

monit start bigchaindb
sleep 10

monit start tendermint
```
