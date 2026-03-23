#!/usr/bin/env bash
#
# init-network.sh
#
# Automates the full BigchainDB 4-node consensus setup:
#   1. Waits for all containers to be healthy
#   2. Extracts node IDs and validator public keys
#   3. Builds a unified genesis.json with all 4 validators
#   4. Distributes genesis.json and configures config.toml
#   5. Resets and restarts all nodes with the new configuration
#
# Prerequisites: docker, jq, curl
#
set -euo pipefail

CONTAINERS=("coordinator1" "member2" "member3" "member4")
MONIKERS=("Coordinator1" "Member2" "Member3" "Member4")
HOST_PORTS=(9984 9986 9988 9990)
MAX_WAIT=60    # seconds to wait per node
TMP_DIR=$(mktemp -d)

trap "rm -rf $TMP_DIR" EXIT

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
for cmd in docker jq curl; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: '$cmd' is required but not installed."
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# 1. Wait for all containers to respond on their BigchainDB API
# ---------------------------------------------------------------------------
wait_for_nodes() {
    echo "[1/6] Waiting for nodes to become ready..."
    for i in "${!CONTAINERS[@]}"; do
        local name="${CONTAINERS[$i]}"
        local port="${HOST_PORTS[$i]}"
        local elapsed=0
        while true; do
            if curl -sf "http://localhost:${port}/" >/dev/null 2>&1; then
                echo "  ✓ ${name} is ready (port ${port})"
                break
            fi
            if [ "$elapsed" -ge "$MAX_WAIT" ]; then
                echo "  ✗ ${name} did not become ready within ${MAX_WAIT}s"
                exit 1
            fi
            sleep 5
            elapsed=$((elapsed + 5))
        done
    done
}

# ---------------------------------------------------------------------------
# 2. Extract node IDs and validator public keys
# ---------------------------------------------------------------------------
declare -A NODE_IDS
declare -A PUB_KEYS

extract_node_info() {
    echo "[2/6] Extracting node IDs and public keys..."
    for c in "${CONTAINERS[@]}"; do
        NODE_IDS[$c]=$(docker exec "$c" tendermint show_node_id 2>/dev/null | tr -d '[:space:]')
        PUB_KEYS[$c]=$(docker exec "$c" cat /tendermint/config/priv_validator.json \
            | jq -r '.pub_key.value')
        echo "  ${c}: id=${NODE_IDS[$c]:0:12}... pubkey=${PUB_KEYS[$c]:0:20}..."
    done
}

# ---------------------------------------------------------------------------
# 3. Build unified genesis.json with all 4 validators
# ---------------------------------------------------------------------------
build_genesis() {
    echo "[3/6] Building unified genesis.json..."

    local base_genesis
    base_genesis=$(docker exec coordinator1 cat /tendermint/config/genesis.json)

    # Build the validators array
    local validators="[]"
    for c in "${CONTAINERS[@]}"; do
        validators=$(echo "$validators" | jq \
            --arg key "${PUB_KEYS[$c]}" \
            --arg name "$c" \
            '. + [{
                "pub_key": {
                    "type": "tendermint/PubKeyEd25519",
                    "value": $key
                },
                "power": "10",
                "name": $name
            }]')
    done

    # Merge validators into the base genesis
    echo "$base_genesis" \
        | jq --argjson vals "$validators" '.validators = $vals' \
        > "${TMP_DIR}/genesis.json"

    local count
    count=$(jq '.validators | length' "${TMP_DIR}/genesis.json")
    echo "  ✓ genesis.json created with ${count} validators"
}

# ---------------------------------------------------------------------------
# 4. Stop services on all nodes
# ---------------------------------------------------------------------------
stop_services() {
    echo "[4/6] Stopping services on all nodes..."
    for c in "${CONTAINERS[@]}"; do
        docker exec "$c" bash -c "monit stop all" 2>/dev/null || true
        echo "  ✓ ${c} services stopped"
    done
    sleep 5
}

# ---------------------------------------------------------------------------
# 5. Reset state, distribute config, apply settings
# ---------------------------------------------------------------------------
configure_nodes() {
    echo "[5/6] Configuring nodes..."
    for i in "${!CONTAINERS[@]}"; do
        local c="${CONTAINERS[$i]}"
        local moniker="${MONIKERS[$i]}"

        echo "  Configuring ${c}..."

        # Reset Tendermint data (keeps keys intact)
        docker exec "$c" tendermint unsafe_reset_all 2>/dev/null || true

        # Copy the unified genesis.json
        docker cp "${TMP_DIR}/genesis.json" "${c}:/tendermint/config/genesis.json"

        # Build persistent_peers string (all nodes except self)
        local peers=""
        for j in "${!CONTAINERS[@]}"; do
            if [ "$i" != "$j" ]; then
                local other="${CONTAINERS[$j]}"
                local peer="${NODE_IDS[$other]}@${other}:26656"
                peers="${peers:+${peers},}${peer}"
            fi
        done

        # Apply all config.toml settings in a single exec
        docker exec "$c" bash -c "
            sed -i 's|^moniker = .*|moniker = \"${moniker}\"|'                     /tendermint/config/config.toml
            sed -i 's|^persistent_peers = .*|persistent_peers = \"${peers}\"|'      /tendermint/config/config.toml
            sed -i 's|^addr_book_strict = .*|addr_book_strict = false|'             /tendermint/config/config.toml
            sed -i 's|^send_rate = .*|send_rate = 102400000|'                       /tendermint/config/config.toml
            sed -i 's|^recv_rate = .*|recv_rate = 102400000|'                       /tendermint/config/config.toml
            sed -i 's|^create_empty_blocks = .*|create_empty_blocks = false|'       /tendermint/config/config.toml
            sed -i 's|^log_level = .*|log_level = \"main:info,state:info,*:error\"|' /tendermint/config/config.toml
        "

        # Reset MongoDB to avoid hash mismatches
        docker exec "$c" bash -c "mongo --eval 'db.dropDatabase()' bigchain" 2>/dev/null || true

        # Re-initialize BigchainDB
        docker exec "$c" bigchaindb init 2>/dev/null || true

        # Fix permissions
        docker exec "$c" bash -c "chmod -R 755 /tendermint"

        echo "  ✓ ${c} configured (moniker=${moniker}, peers=${#CONTAINERS[@]}-1 nodes)"
    done
}

# ---------------------------------------------------------------------------
# 6. Restart services in the correct order
# ---------------------------------------------------------------------------
start_services() {
    echo "[6/6] Restarting services..."

    for c in "${CONTAINERS[@]}"; do
        docker exec "$c" bash -c "monit start all"
        echo "  ✓ ${c} services started"
    done
    echo "  Waiting for services to initialize..."
    sleep 15
}

# ---------------------------------------------------------------------------
# 7. Verify consensus
# ---------------------------------------------------------------------------
verify_consensus() {
    echo ""
    echo "Verifying network health..."
    local all_ok=true
    for i in "${!CONTAINERS[@]}"; do
        local name="${CONTAINERS[$i]}"
        local port="${HOST_PORTS[$i]}"
        if curl -sf "http://localhost:${port}/" >/dev/null 2>&1; then
            local height
            height=$(curl -sf "http://localhost:$((26657 + i))/" 2>/dev/null \
                | jq -r '.result.sync_info.latest_block_height // "N/A"' 2>/dev/null || echo "N/A")
            echo "  ✓ ${name}: online (block height: ${height})"
        else
            echo "  ✗ ${name}: not responding"
            all_ok=false
        fi
    done

    if $all_ok; then
        echo ""
        echo "=== Network initialization complete ==="
    else
        echo ""
        echo "=== WARNING: Some nodes are not responding ==="
        echo "    Run 'docker compose logs' to investigate."
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
echo "============================================================"
echo "  BigchainDB 4-Node Network Initialization"
echo "============================================================"
echo ""

wait_for_nodes
extract_node_info
build_genesis
stop_services
configure_nodes
start_services
verify_consensus

echo ""
echo "  Coordinator1 API : http://localhost:9984"
echo "  Member2 API      : http://localhost:9986"
echo "  Member3 API      : http://localhost:9988"
echo "  Member4 API      : http://localhost:9990"
echo "  Dashboard        : http://localhost:8501"
echo ""
