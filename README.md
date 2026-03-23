# BigchainDB Decentralized Database Demo

A fully automated, production-style demo of a **4-node BigchainDB blockchain network** featuring Byzantine Fault Tolerant (BFT) consensus, dual dashboards (Streamlit + React), and complete tooling for creating, transferring, and querying digital assets across a distributed ledger.

https://github.com/user-attachments/assets/576ef115-ec14-49de-b67f-fd25149b4461

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/YOUR_USERNAME/BigChainDB?quickstart=1)

---

## Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [What the Demo Shows](#what-the-demo-shows)
- [Dashboards](#dashboards)
- [Network Configuration](#network-configuration)
  - [genesis.json — Validators & Voting Power](#genesisjson--validators--voting-power)
  - [config.toml — Tendermint Parameters](#configtoml--tendermint-parameters)
  - [Consensus Parameters](#consensus-parameters)
- [Commands Reference](#commands-reference)
- [API Reference](#api-reference)
- [Advanced Operations](#advanced-operations)
- [Python Environment & Dependencies](#python-environment--dependencies)
- [Project Structure](#project-structure)
- [Port Reference](#port-reference)
- [Troubleshooting](#troubleshooting)
- [Branch Strategy](#branch-strategy)
- [License](#license)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       Docker Network  (bigchaindb-net)                       │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ coordinator1  │  │   member2    │  │   member3    │  │   member4    │    │
│  │              │  │              │  │              │  │              │    │
│  │  BigchainDB  │  │  BigchainDB  │  │  BigchainDB  │  │  BigchainDB  │    │
│  │  MongoDB     │  │  MongoDB     │  │  MongoDB     │  │  MongoDB     │    │
│  │  Tendermint  │  │  Tendermint  │  │  Tendermint  │  │  Tendermint  │    │
│  │              │  │              │  │              │  │              │    │
│  │  API  :9984  │  │  API  :9986  │  │  API  :9988  │  │  API  :9990  │    │
│  │  WS   :9985  │  │  WS   :9987  │  │  WS   :9989  │  │  WS   :9991  │    │
│  │  RPC  :26657 │  │  RPC  :26658 │  │  RPC  :26659 │  │  RPC  :26660 │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         └────────────────┴────────────────┴────────────────┘                │
│                    Tendermint BFT Consensus  (P2P :26656)                    │
│                                                                              │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────┐      │
│  │   Streamlit Dashboard       │  │   React Dashboard (Vite)         │      │
│  │   Python · port 8501        │  │   Node.js · port 5173            │      │
│  └─────────────────────────────┘  └──────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────────┘
```

Each node runs the `bigchaindb/bigchaindb:all-in-one` Docker image containing:

| Component      | Role                                                        |
| -------------- | ----------------------------------------------------------- |
| **BigchainDB** | Immutable asset API — CREATE, TRANSFER, and query operations |
| **MongoDB**    | Persistent storage layer for blocks and transactions         |
| **Tendermint** | Byzantine Fault Tolerant consensus engine (⅔+1 agreement)   |
| **Monit**      | Process supervisor managing all services inside the container |

### How Consensus Works

BigchainDB uses **Tendermint BFT consensus**, which guarantees:

- **Immediate finality**: once a block is committed, it cannot be reverted
- **Byzantine tolerance**: the network tolerates up to **⅓ of nodes** behaving maliciously (with 4 nodes, 1 can fail)
- **Deterministic**: all honest nodes process the same transactions in the same order

The **coordinator** node bootstraps the network: its `genesis.json` (containing all validators' public keys and voting power) is distributed to every node before consensus begins.

---

## Quick Start

### Option 1 — One Command (Docker Compose)

**Prerequisites:** Docker, Docker Compose, `jq`, `curl`.

```bash
git clone https://github.com/YOUR_USERNAME/BigChainDB.git
cd BigChainDB
./scripts/start.sh
```

This script:
1. Pulls and starts 4 BigchainDB containers
2. Waits for all nodes to be healthy
3. Extracts validator keys and builds a unified `genesis.json`
4. Configures Tendermint peers, monikers, and consensus parameters
5. Resets and restarts all services in the correct order
6. Launches the Streamlit dashboard

Open **http://localhost:8080** when it finishes.

### Option 2 — GitHub Codespaces (zero local setup)

Click the badge above (or **Code → Codespaces → New codespace**).
The dev container automatically builds the environment, starts all nodes, and opens the dashboard.

### Option 3 — React Dashboard (modern UI)

```bash
# Start the blockchain nodes
docker compose up -d coordinator1 member2 member3 member4
bash scripts/init-network.sh

# Start the React frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** for the React dashboard with dark/minimal design.

### Option 4 — Streamlit locally (nodes in Docker)

```bash
docker compose up -d coordinator1 member2 member3 member4
bash scripts/init-network.sh

# Create Conda environment (Python 3.6.13)
conda env create -f environment.yml
conda activate BigChainDB

streamlit run src/DecentralizedDatabaseDEMO.py
```

### Common Commands

```bash
# Start everything (nodes + init + dashboard)
./scripts/start.sh

# Tear down and start fresh
./scripts/start.sh --clean

# Stop all containers
docker compose down

# Stop and remove all data (volumes)
docker compose down -v --remove-orphans

# View logs
docker compose logs -f coordinator1
docker compose logs -f dashboard

# Restart a specific node
docker compose restart member2
```

---

## What the Demo Shows

| Scenario                  | Description                                                                   |
| ------------------------- | ----------------------------------------------------------------------------- |
| **Network Overview**      | Real-time status of all 4 nodes with block height, Tendermint state, and uptime |
| **Simple Broadcast**      | Create an asset on one node, verify it replicates to all 4 within seconds      |
| **Transfer Chain**        | Transfer ownership across nodes: Alice → Bob → Carol → Dave                   |
| **Parallel Transactions** | Create 4 assets simultaneously on different nodes                              |
| **Cross-Node Queries**    | Query any transaction from any node to demonstrate data consistency            |
| **Export**                | Download transaction history as CSV or JSON                                    |

---

## Dashboards

### Streamlit Dashboard (port 8501)

Python-based dashboard with 5 pages:
- **Network Overview** — node status, block heights, success rates
- **Create Asset** — form-based asset creation with type selection
- **Transfer Asset** — ownership transfer with recipient keypair generation
- **Query Transaction** — look up any TX by ID, verify across all nodes
- **Transaction History** — table view with CSV/JSON export

### React Dashboard (port 5173)

Modern React + Vite frontend with dark/minimal design:
- Same 5 pages as Streamlit but with a professional UI
- Auto-refreshing node status every 30 seconds
- Transaction persistence in localStorage
- Responsive layout with sidebar navigation

---

## Network Configuration

### genesis.json — Validators & Voting Power

The `genesis.json` file defines the initial state of the blockchain, including which nodes can validate (vote on) transactions and their **voting power** (weight).

#### Structure

```json
{
  "genesis_time": "2025-11-16T23:37:54.466847445Z",
  "chain_id": "test-chain-274NpV",
  "consensus_params": {
    "block_size_params": {
      "max_bytes": "22020096",
      "max_txs": "10000",
      "max_gas": "-1"
    },
    "tx_size_params": {
      "max_bytes": "10240",
      "max_gas": "-1"
    },
    "block_gossip_params": {
      "block_part_size_bytes": "65536"
    },
    "evidence_params": {
      "max_age": "100000"
    }
  },
  "validators": [
    {
      "pub_key": {
        "type": "tendermint/PubKeyEd25519",
        "value": "wfWpYJ1zbUoDeieMSdBSSLV3HEdnTKHeOZHCOvi9Z2E="
      },
      "power": "10",
      "name": "coordinator1"
    },
    {
      "pub_key": {
        "type": "tendermint/PubKeyEd25519",
        "value": "PAK1enS0Hkv38feNbVhYNInZJ80fXd03xwcu0yL5vbE="
      },
      "power": "10",
      "name": "member2"
    }
  ],
  "app_hash": ""
}
```

#### Changing Validator Voting Power

Each validator has a `"power"` field that determines its weight in the consensus process. By default, all 4 nodes have `"power": "10"` (equal weight). You can customize this to simulate real-world scenarios.

**Example: Give the coordinator double voting power**

Edit `scripts/init-network.sh`, in the `build_genesis()` function, change the power assignment:

```bash
# In build_genesis(), replace the static power with per-node logic:
local power="10"
if [ "$c" == "coordinator1" ]; then
    power="20"
fi

validators=$(echo "$validators" | jq \
    --arg key "${PUB_KEYS[$c]}" \
    --arg name "$c" \
    --arg power "$power" \
    '. + [{
        "pub_key": {
            "type": "tendermint/PubKeyEd25519",
            "value": $key
        },
        "power": $power,
        "name": $name
    }]')
```

**Or modify the genesis.json directly** after `init-network.sh` runs:

```bash
# Extract the current genesis from coordinator1
docker cp coordinator1:/tendermint/config/genesis.json ./genesis.json

# Edit the power values (e.g., coordinator1 gets power 20, others get 10)
jq '.validators[0].power = "20"' genesis.json > genesis_modified.json

# Distribute to all nodes
for node in coordinator1 member2 member3 member4; do
    docker cp genesis_modified.json ${node}:/tendermint/config/genesis.json
done

# Restart the network
./scripts/start.sh --clean
```

**Understanding voting power:**

| Configuration | coordinator1 | member2 | member3 | member4 | Total | BFT Threshold (⅔+1) |
|---|---|---|---|---|---|---|
| Equal (default) | 10 | 10 | 10 | 10 | 40 | 27 |
| Coordinator heavy | 20 | 10 | 10 | 10 | 50 | 34 |
| Weighted | 40 | 20 | 20 | 20 | 100 | 67 |

> **BFT Rule**: A block is committed when validators with >⅔ of total voting power agree. With equal power (10 each, total 40), you need 27+ power to commit → 3 out of 4 nodes must agree.

**Verify current voting power:**

```bash
# Check validators and their voting power
curl -s http://localhost:26657/validators | jq '.result.validators[] | {address: .address, voting_power: .voting_power}'

# Check from BigchainDB API
curl -s http://localhost:9984/api/v1/validators
```

---

### config.toml — Tendermint Parameters

The `config.toml` file controls how each Tendermint node operates. The init script sets these automatically, but you can customize them.

#### View current config

```bash
docker exec coordinator1 cat /tendermint/config/config.toml
```

#### Key parameters

| Parameter | Default | Description |
|---|---|---|
| `moniker` | `"Coordinator1"` | Human-readable node name |
| `persistent_peers` | *(auto-configured)* | Nodes to always maintain connections with |
| `addr_book_strict` | `false` | Allow private/local IP addresses (required for Docker) |
| `send_rate` | `102400000` | Max bytes/sec for outgoing data (100 MB/s) |
| `recv_rate` | `102400000` | Max bytes/sec for incoming data (100 MB/s) |
| `create_empty_blocks` | `false` | Don't create blocks when there are no transactions |
| `log_level` | `"main:info,state:info,*:error"` | Logging verbosity |

#### Modify a parameter on a running node

```bash
# Example: enable empty block creation on coordinator1
docker exec coordinator1 bash -c "
    sed -i 's/^create_empty_blocks = .*/create_empty_blocks = true/' /tendermint/config/config.toml
"

# Restart the node to apply
docker compose restart coordinator1
```

#### Modify peer connections

```bash
# Get node IDs
docker exec coordinator1 tendermint show_node_id
docker exec member2 tendermint show_node_id
docker exec member3 tendermint show_node_id
docker exec member4 tendermint show_node_id

# Format: NODE_ID@container_name:26656
# Example peer string for coordinator1 (all other nodes):
# "abc123@member2:26656,def456@member3:26656,ghi789@member4:26656"

docker exec coordinator1 bash -c "
    sed -i 's/^persistent_peers = .*/persistent_peers = \"PEER_STRING_HERE\"/' /tendermint/config/config.toml
"
```

---

### Consensus Parameters

These are set in `genesis.json` under `consensus_params` and affect the entire network.

| Parameter | Default | Description |
|---|---|---|
| `block_size_params.max_bytes` | `22020096` (21 MB) | Maximum block size in bytes |
| `block_size_params.max_txs` | `10000` | Maximum transactions per block |
| `block_size_params.max_gas` | `-1` (unlimited) | Maximum gas per block |
| `tx_size_params.max_bytes` | `10240` (10 KB) | Maximum single transaction size |
| `tx_size_params.max_gas` | `-1` (unlimited) | Maximum gas per transaction |
| `evidence_params.max_age` | `100000` | Maximum age of evidence (in blocks) |
| `block_gossip_params.block_part_size_bytes` | `65536` (64 KB) | Size of block parts for gossip protocol |

**Modify consensus parameters:**

```bash
# Extract genesis
docker cp coordinator1:/tendermint/config/genesis.json ./genesis.json

# Example: increase max transactions per block to 50000
jq '.consensus_params.block_size_params.max_txs = "50000"' genesis.json > genesis_modified.json

# Example: increase max block size to 42 MB
jq '.consensus_params.block_size_params.max_bytes = "44040192"' genesis.json > genesis_modified.json

# IMPORTANT: genesis.json must be identical on ALL nodes
for node in coordinator1 member2 member3 member4; do
    docker cp genesis_modified.json ${node}:/tendermint/config/genesis.json
done

# Full reset required after changing genesis
./scripts/start.sh --clean
```

---

## Commands Reference

### Docker Compose

```bash
# Start all services (4 nodes + dashboard)
docker compose up -d

# Start only the blockchain nodes (no dashboard)
docker compose up -d coordinator1 member2 member3 member4

# Start with build (after Dockerfile changes)
docker compose up -d --build dashboard

# Rebuild a specific service without cache
docker compose build --no-cache dashboard

# Stop all services
docker compose down

# Stop and destroy all data
docker compose down -v --remove-orphans

# View running containers
docker compose ps

# Follow logs for a specific service
docker compose logs -f coordinator1

# Follow logs for all services
docker compose logs -f

# Restart a service
docker compose restart member2

# Scale (not applicable here, but for reference)
docker compose up -d --scale member2=1
```

### Container Operations

```bash
# Enter a container shell
docker exec -it coordinator1 /bin/bash

# Check monit services status
docker exec coordinator1 monit summary

# Stop all services in a container
docker exec coordinator1 monit stop all

# Start all services in a container
docker exec coordinator1 monit start all

# View Tendermint node ID
docker exec coordinator1 tendermint show_node_id

# View validator private key info
docker exec coordinator1 cat /tendermint/config/priv_validator.json

# View genesis configuration
docker exec coordinator1 cat /tendermint/config/genesis.json

# View Tendermint configuration
docker exec coordinator1 cat /tendermint/config/config.toml

# Reset Tendermint state (dangerous — removes blockchain history)
docker exec coordinator1 tendermint unsafe_reset_all

# Reset MongoDB
docker exec coordinator1 mongo --eval 'db.dropDatabase()' bigchain

# Reinitialize BigchainDB
docker exec coordinator1 bigchaindb init

# View container resource usage
docker stats coordinator1 member2 member3 member4
```

### Network Inspection

```bash
# Inspect Docker network
docker network inspect bigchaindb_bigchaindb-net

# Get container IP addresses
docker inspect -f '{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
    coordinator1 member2 member3 member4

# Check inter-node connectivity
docker exec coordinator1 ping -c 1 member2
```

### Scripts

```bash
# One-click start (nodes + init + dashboard)
./scripts/start.sh

# Clean start (destroys all data first)
./scripts/start.sh --clean

# Run only the network initialization (nodes must already be running)
bash scripts/init-network.sh
```

---

## API Reference

### BigchainDB REST API

Each node exposes the BigchainDB HTTP API. Replace the port based on the node:

| Node | Base URL |
|---|---|
| coordinator1 | `http://localhost:9984` |
| member2 | `http://localhost:9986` |
| member3 | `http://localhost:9988` |
| member4 | `http://localhost:9990` |

```bash
# Check node health
curl http://localhost:9984/

# Get API info
curl http://localhost:9984/api/v1/

# Get a transaction by ID
curl http://localhost:9984/api/v1/transactions/<TX_ID>

# Search assets by keyword
curl "http://localhost:9984/api/v1/assets/?search=myasset"

# Search metadata by keyword
curl "http://localhost:9984/api/v1/metadata/?search=category"

# Get outputs for a public key
curl "http://localhost:9984/api/v1/outputs/?public_key=<PUBLIC_KEY>"

# Get spent/unspent outputs
curl "http://localhost:9984/api/v1/outputs/?public_key=<PUBLIC_KEY>&spent=false"

# Get current validators
curl http://localhost:9984/api/v1/validators

# List blocks (by transaction ID)
curl "http://localhost:9984/api/v1/blocks/?transaction_id=<TX_ID>"
```

### Tendermint RPC API

```bash
# Node status (block height, sync info, validator info)
curl http://localhost:26657/status

# Network info (connected peers)
curl http://localhost:26657/net_info

# Current validators and voting power
curl http://localhost:26657/validators

# Get a specific block
curl "http://localhost:26657/block?height=5"

# Get block results
curl "http://localhost:26657/block_results?height=5"

# Consensus state
curl http://localhost:26657/consensus_state

# Dump consensus state (detailed)
curl http://localhost:26657/dump_consensus_state

# Get genesis
curl http://localhost:26657/genesis

# Unconfirmed transactions in mempool
curl http://localhost:26657/unconfirmed_txs

# Number of unconfirmed transactions
curl http://localhost:26657/num_unconfirmed_txs

# Node health
curl http://localhost:26657/health

# Get ABCI info
curl http://localhost:26657/abci_info
```

### WebSocket API

BigchainDB exposes WebSocket endpoints for real-time transaction streaming:

```
ws://localhost:9985/api/v1/streams/valid_transactions
ws://localhost:9987/api/v1/streams/valid_transactions  (member2)
ws://localhost:9989/api/v1/streams/valid_transactions  (member3)
ws://localhost:9991/api/v1/streams/valid_transactions  (member4)
```

```python
# Example: listen for new transactions
import websocket
ws = websocket.WebSocket()
ws.connect('ws://localhost:9985/api/v1/streams/valid_transactions')
while True:
    result = ws.recv()
    print(result)
```

---

## Advanced Operations

### Adding a 5th Node

```bash
# 1. Add the service to docker-compose.yml
# 2. Start the new node
docker compose up -d member5

# 3. Get its validator key
docker exec member5 cat /tendermint/config/priv_validator.json | jq '.pub_key.value'
docker exec member5 tendermint show_node_id

# 4. Add it to genesis.json validators array with the desired power
# 5. Update persistent_peers on all nodes to include member5
# 6. Distribute the new genesis.json to all nodes
# 7. Reset and restart the entire network
./scripts/start.sh --clean
```

### Removing a Validator

```bash
# Remove a validator from genesis.json
jq 'del(.validators[] | select(.name == "member4"))' genesis.json > genesis_modified.json

# Distribute and restart
for node in coordinator1 member2 member3; do
    docker cp genesis_modified.json ${node}:/tendermint/config/genesis.json
done
```

### Simulating Node Failure (BFT Test)

```bash
# Stop one node to test fault tolerance (network should continue)
docker compose stop member4

# Verify the network still commits blocks (3 out of 4 nodes = 75% > 66.7%)
curl -s http://localhost:26657/status | jq '.result.sync_info.latest_block_height'

# Stop a second node (network should HALT — only 50% remaining)
docker compose stop member3

# Verify: block height stops increasing
curl -s http://localhost:26657/status | jq '.result.sync_info.latest_block_height'

# Restart nodes to resume
docker compose start member3 member4
```

### Backup and Restore

```bash
# Backup all volumes
docker run --rm -v bigchaindb_coordinator1-db:/data -v $(pwd):/backup \
    alpine tar czf /backup/coordinator1-db.tar.gz -C /data .

# Restore
docker run --rm -v bigchaindb_coordinator1-db:/data -v $(pwd):/backup \
    alpine tar xzf /backup/coordinator1-db.tar.gz -C /data
```

### Performance Testing

```bash
# Run the CLI integration test (3 automated scenarios)
python src/rapidDemo.py

# Scenarios executed:
# 1. Simple Broadcast — create on one node, verify on all 4
# 2. Transfer Chain — Alice → Bob → Carol → Dave across nodes
# 3. Parallel Transactions — 4 simultaneous creates on different nodes
```

---

## Python Environment & Dependencies

> **Python 3.6.13** is required for the Conda environment.
> BigchainDB's driver and cryptographic dependencies are pinned to exact versions tested against Python 3.6.

### Conda Environment (Recommended)

```bash
# Create the environment from the pinned export
conda env create -f environment.yml

# Activate
conda activate BigChainDB

# Verify Python version
python --version  # Should show 3.6.13
```

### Key Dependencies

| Package              | Version | Purpose                                     |
| -------------------- | ------- | ------------------------------------------- |
| `bigchaindb-driver`  | 0.6.2   | BigchainDB transaction driver (CREATE/TRANSFER) |
| `streamlit`          | 1.10.0  | Dashboard UI framework                       |
| `requests`           | 2.27.1  | HTTP client for API calls                    |
| `pandas`             | 1.1.5   | Data processing for tables and exports       |
| `numpy`              | 1.19.5  | Numerical computing (pandas dependency)      |
| `pynacl`             | 1.1.2   | Ed25519 cryptographic signing                |
| `cryptoconditions`   | 0.8.0   | Crypto-conditions for transaction fulfillment |
| `pysha3`             | 1.0.2   | SHA3 hashing                                 |
| `base58`             | 1.0.3   | Base58 encoding for keys                     |

See [`environment.yml`](environment.yml) for the complete pinned Conda environment.
See [`requirements.txt`](requirements.txt) for pip-installable dependencies (Docker containers).

### React Frontend Dependencies

```bash
cd frontend
npm install       # Install dependencies
npm run dev       # Development server (port 5173)
npm run build     # Production build to dist/
npm run preview   # Preview production build
```

---

## Project Structure

```
BigChainDB/
├── .devcontainer/
│   ├── devcontainer.json          # GitHub Codespaces config (auto-start)
│   └── Dockerfile                 # Python 3.9 + build deps for Codespaces
├── docker/
│   └── streamlit.Dockerfile       # Streamlit dashboard container (Python 3.6)
├── frontend/                      # React + Vite dashboard
│   ├── src/
│   │   ├── api/
│   │   │   └── bigchaindb.js      # BigchainDB API client
│   │   ├── components/
│   │   │   └── Sidebar.jsx        # Navigation + node status
│   │   ├── pages/
│   │   │   ├── Overview.jsx       # Network status dashboard
│   │   │   ├── CreateAsset.jsx    # Asset creation form
│   │   │   ├── TransferAsset.jsx  # Asset transfer form
│   │   │   ├── QueryTransaction.jsx # Transaction lookup
│   │   │   └── History.jsx        # Transaction history + export
│   │   ├── App.jsx                # Router + state management
│   │   ├── main.jsx               # Entry point
│   │   └── index.css              # Global styles (dark theme)
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── start.sh                   # One-click launcher (nodes + init + dashboard)
│   └── init-network.sh            # Consensus network bootstrap automation
├── src/
│   ├── DecentralizedDatabaseDEMO.py   # Streamlit dashboard (5 pages)
│   └── rapidDemo.py                   # CLI integration test (3 scenarios)
├── documentation/
│   └── doc.md                     # Original manual setup reference
├── docker-compose.yml             # Full 4-node + dashboard stack
├── environment.yml                # Conda environment (Python 3.6.13, pinned)
├── requirements.txt               # Pip dependencies (for Docker containers)
└── README.md
```

---

## Port Reference

| Service        | BigchainDB API | WebSocket API | Tendermint RPC | Tendermint P2P |
| -------------- | -------------- | ------------- | -------------- | -------------- |
| coordinator1   | 9984           | 9985          | 26657          | 26656 (internal) |
| member2        | 9986           | 9987          | 26658          | 26656 (internal) |
| member3        | 9988           | 9989          | 26659          | 26656 (internal) |
| member4        | 9990           | 9991          | 26660          | 26656 (internal) |
| **React (Docker)** | **8080**  | —             | —              | — |
| **React**      | **5173**       | —             | —              | — |

---

## Troubleshooting

### Nodes not starting

```bash
# Check container logs
docker compose logs coordinator1

# Verify Docker is running
docker info

# Check port conflicts
ss -tlnp | grep -E '9984|9986|9988|9990|26657'
```

### Health check failures

```bash
# Test node manually
curl -sf http://localhost:9984/ && echo "OK" || echo "FAIL"

# Check health check status in Docker
docker inspect --format='{{.State.Health.Status}}' coordinator1

# View recent health check results
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' coordinator1
```

### Consensus not starting

```bash
# Verify all nodes have the same genesis.json
for node in coordinator1 member2 member3 member4; do
    echo "=== $node ==="
    docker exec $node cat /tendermint/config/genesis.json | jq '.validators | length'
done

# Check peer connections
curl -s http://localhost:26657/net_info | jq '.result.n_peers'

# Verify persistent_peers is configured
docker exec coordinator1 grep persistent_peers /tendermint/config/config.toml
```

### Dashboard build fails

```bash
# Rebuild without cache
docker compose build --no-cache dashboard

# Check Python version in container
docker exec bigchaindb-dashboard python --version

# Check installed packages
docker exec bigchaindb-dashboard pip list
```

### Block height stuck at 0 or N/A

```bash
# Full reset of the network
./scripts/start.sh --clean

# Or manual reset per node:
docker exec coordinator1 bash -c "
    monit stop all
    sleep 5
    tendermint unsafe_reset_all
    mongo --eval 'db.dropDatabase()' bigchain
    bigchaindb init
    chmod -R 755 /tendermint
    monit start all
"
```

### Transaction not found on other nodes

```bash
# Transactions need a few seconds to propagate
# Wait and retry:
sleep 10
curl http://localhost:9986/api/v1/transactions/<TX_ID>

# Check if nodes are in sync
for port in 26657 26658 26659 26660; do
    echo "Port $port: $(curl -s http://localhost:$port/status | jq -r '.result.sync_info.latest_block_height')"
done
```

---

## Branch Strategy

| Branch        | Purpose                                              |
| ------------- | ---------------------------------------------------- |
| `main`        | Stable, production-ready code. Protected branch.     |
| `develop`     | Integration branch — features merge here first.      |
| `feature/*`   | New features, branched from `develop`.               |
| `fix/*`       | Bug fixes, branched from `develop`.                  |

**Workflow:**
1. `git checkout -b feature/my-feature develop`
2. Open a Pull Request targeting `develop`
3. After review, merge into `develop`
4. Release: merge `develop` → `main` and tag the version

---

## License

MIT
