#!/usr/bin/env bash
#
# start.sh - One-click launcher for the BigchainDB demo environment.
#
# Usage:
#   ./scripts/start.sh          Start everything (nodes + init + dashboard)
#   ./scripts/start.sh --clean  Tear down and start fresh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# Handle --clean flag
# ---------------------------------------------------------------------------
if [[ "${1:-}" == "--clean" ]]; then
    echo "Tearing down existing environment..."
    docker compose down -v --remove-orphans 2>/dev/null || true
    echo "  ✓ Clean slate"
    echo ""
fi

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
echo "============================================================"
echo "  BigchainDB Demo - Automated Launcher"
echo "============================================================"
echo ""

for cmd in docker jq curl; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: '$cmd' is required. Please install it first."
        exit 1
    fi
done

if ! docker info &>/dev/null; then
    echo "ERROR: Docker daemon is not running."
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. Start BigchainDB nodes
# ---------------------------------------------------------------------------
echo "[1/3] Starting BigchainDB nodes..."
docker compose up -d coordinator1 member2 member3 member4
echo "  ✓ Containers started"
echo ""

# ---------------------------------------------------------------------------
# 2. Initialize consensus network
# ---------------------------------------------------------------------------
echo "[2/3] Initializing consensus network..."
bash "$SCRIPT_DIR/init-network.sh"
echo ""

# ---------------------------------------------------------------------------
# 3. Start React dashboard
# ---------------------------------------------------------------------------
echo "[3/3] Building and starting React dashboard..."
docker compose up -d --build dashboard
echo "  ✓ Dashboard container started"
echo ""

# ---------------------------------------------------------------------------
# Final status
# ---------------------------------------------------------------------------
echo "============================================================"
echo "  All services are running!"
echo ""
echo "  Dashboard  : http://localhost:8080"
echo "  Node APIs  : http://localhost:9984  (coordinator1)"
echo "               http://localhost:9986  (member2)"
echo "               http://localhost:9988  (member3)"
echo "               http://localhost:9990  (member4)"
echo ""
echo "  Useful commands:"
echo "    docker compose logs -f dashboard    # Dashboard logs"
echo "    docker compose logs -f coordinator1 # Node logs"
echo "    docker compose down                 # Stop everything"
echo "    ./scripts/start.sh --clean          # Full reset"
echo "============================================================"
