import streamlit as st
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
import time
import json
import requests
import pandas as pd
from typing import Dict, List, Optional, Tuple

# Page documentation
st.set_page_config(
    page_title="BigchainDB Network Dashboard",
    page_icon="🔗",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2ca02c;
        padding: 0.5rem 0;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
NODES = [
    {'name': 'coordinator1', 'url': 'http://localhost:9984', 'tendermint': 'http://localhost:26657'},
    {'name': 'member2', 'url': 'http://localhost:9986', 'tendermint': 'http://localhost:26658'},
    {'name': 'member3', 'url': 'http://localhost:9988', 'tendermint': 'http://localhost:26659'},
    {'name': 'member4', 'url': 'http://localhost:9990', 'tendermint': 'http://localhost:26660'}
]

TIMEOUT = 30

# Initialize session state
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'keypairs' not in st.session_state:
    st.session_state.keypairs = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Network Overview"


# Helper Functions
def check_node_status(node: Dict) -> Dict:
    """Check the status of a BigchainDB node"""
    try:
        response = requests.get(f"{node['url']}/api/v1/", timeout=5)
        bigchaindb_ok = response.status_code == 200

        try:
            tendermint_response = requests.get(f"{node['tendermint']}/status", timeout=5)
            tendermint_ok = tendermint_response.status_code == 200
            tendermint_data = tendermint_response.json()
            block_height = tendermint_data['result']['sync_info']['latest_block_height']
        except:
            tendermint_ok = False
            block_height = "N/A"

        return {
            'name': node['name'],
            'url': node['url'],
            'status': 'online' if bigchaindb_ok else 'offline',
            'bigchaindb': bigchaindb_ok,
            'tendermint': tendermint_ok,
            'block_height': block_height
        }
    except:
        return {
            'name': node['name'],
            'url': node['url'],
            'status': 'unreachable',
            'bigchaindb': False,
            'tendermint': False,
            'block_height': "N/A"
        }


def create_asset_transaction(node_url: str, asset_data: Dict, metadata: Dict) -> Tuple[Optional[str], Optional[object]]:
    """Create a CREATE transaction"""
    try:
        bdb = BigchainDB(node_url)
        bdb.transport.timeout = TIMEOUT

        creator = generate_keypair()

        prepared_tx = bdb.transactions.prepare(
            operation='CREATE',
            signers=creator.public_key,
            asset=asset_data,
            metadata=metadata
        )

        fulfilled_tx = bdb.transactions.fulfill(
            prepared_tx,
            private_keys=creator.private_key
        )

        sent_tx = bdb.transactions.send_commit(fulfilled_tx)

        return sent_tx['id'], creator
    except Exception as e:
        st.error(f"Error creating transaction: {str(e)}")
        return None, None


def transfer_asset(node_url: str, tx_id: str, from_keypair, to_public_key: str, metadata: Dict) -> Optional[str]:
    """Transfer an asset"""
    try:
        bdb = BigchainDB(node_url)
        bdb.transport.timeout = TIMEOUT

        previous_tx = bdb.transactions.retrieve(tx_id)

        if previous_tx['operation'] == 'CREATE':
            asset_id = previous_tx['id']
        else:
            asset_id = previous_tx['asset']['id']

        transfer_asset_data = {'id': asset_id}

        output_index = 0
        output = previous_tx['outputs'][output_index]

        transfer_input = {
            'fulfillment': output['condition']['details'],
            'fulfills': {
                'output_index': output_index,
                'transaction_id': previous_tx['id']
            },
            'owners_before': output['public_keys']
        }

        prepared_transfer_tx = bdb.transactions.prepare(
            operation='TRANSFER',
            asset=transfer_asset_data,
            inputs=transfer_input,
            recipients=to_public_key,
            metadata=metadata
        )

        fulfilled_transfer_tx = bdb.transactions.fulfill(
            prepared_transfer_tx,
            private_keys=from_keypair.private_key
        )

        sent_transfer_tx = bdb.transactions.send_commit(fulfilled_transfer_tx)

        return sent_transfer_tx['id']
    except Exception as e:
        st.error(f"Error transferring asset: {str(e)}")
        return None


def verify_transaction_on_nodes(tx_id: str, nodes_to_check: List[Dict]) -> Dict:
    """Verify transaction on specified nodes"""
    results = {}
    for node in nodes_to_check:
        try:
            bdb = BigchainDB(node['url'])
            bdb.transport.timeout = TIMEOUT
            tx = bdb.transactions.retrieve(tx_id)
            results[node['name']] = {'found': True, 'transaction': tx}
        except:
            results[node['name']] = {'found': False}
    return results


def get_transaction_details(node_url: str, tx_id: str) -> Optional[Dict]:
    """Get transaction details"""
    try:
        bdb = BigchainDB(node_url)
        bdb.transport.timeout = TIMEOUT
        return bdb.transactions.retrieve(tx_id)
    except:
        return None


# Header
st.markdown('<div class="main-header">🔗 BigchainDB Network Dashboard</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Navigation")

    # Page selection
    page = st.radio(
        "Select Page",
        ["📊 Network Overview", "➕ Create Asset", "🔄 Transfer Asset", "🔍 Query Transaction", "📜 Transaction History"]
    )
    st.session_state.current_page = page

    st.markdown("---")
    st.subheader("Network Status")

    if st.button("🔄 Refresh Status"):
        st.experimental_rerun()

    # Check all nodes
    node_statuses = [check_node_status(node) for node in NODES]
    online_count = sum(1 for status in node_statuses if status['status'] == 'online')

    st.metric("Nodes Online", f"{online_count}/4")

    for status in node_statuses:
        if status['status'] == 'online':
            st.success(f"✓ {status['name']}")
        else:
            st.error(f"✗ {status['name']}")

    st.markdown("---")
    st.subheader("Statistics")
    st.metric("Total Transactions", len(st.session_state.transactions))

    if st.button("🧹 Clear History"):
        st.session_state.transactions = []
        st.session_state.keypairs = {}
        st.success("History cleared!")
        time.sleep(1)
        st.experimental_rerun()

# Page 1: Network Overview
if st.session_state.current_page == "📊 Network Overview":
    st.markdown('<div class="sub-header">Network Status Overview</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    metrics = {
        'total_nodes': len(NODES),
        'online_nodes': online_count,
        'total_transactions': len(st.session_state.transactions),
        'success_rate': 0
    }

    if metrics['total_transactions'] > 0:
        successful = sum(1 for tx in st.session_state.transactions if tx.get('status') == 'success')
        metrics['success_rate'] = (successful / metrics['total_transactions']) * 100

    with col1:
        st.metric("Total Nodes", metrics['total_nodes'])
    with col2:
        st.metric("Online Nodes", metrics['online_nodes'])
    with col3:
        st.metric("Total Transactions", metrics['total_transactions'])
    with col4:
        st.metric("Success Rate", f"{metrics['success_rate']:.1f}%")

    st.markdown("---")

    # Node details table
    st.subheader("Node Details")
    df_nodes = pd.DataFrame(node_statuses)
    st.dataframe(df_nodes)

    st.markdown("---")
    st.subheader("Recent Activity")
    if st.session_state.transactions:
        recent = st.session_state.transactions[-5:]
        for tx in reversed(recent):
            st.write(f"**{tx['type']}** - {tx['asset_title']} on {tx['node']} at {tx['timestamp']}")
    else:
        st.info("No transactions yet")

# Page 2: Create Asset
elif st.session_state.current_page == "➕ Create Asset":
    st.markdown('<div class="sub-header">Create New Asset</div>', unsafe_allow_html=True)

    with st.form("create_asset_form"):
        col1, col2 = st.columns(2)

        with col1:
            asset_type = st.selectbox("Asset Type", ["document", "token", "certificate", "custom"])
            asset_title = st.text_input("Asset Title", placeholder="e.g., My Document")
            asset_description = st.text_area("Asset Description", placeholder="Describe your asset...")

        with col2:
            creator_name = st.text_input("Creator Name", placeholder="e.g., Alice")
            metadata_key = st.text_input("Metadata Key", placeholder="e.g., category")
            metadata_value = st.text_input("Metadata Value", placeholder="e.g., finance")

        node_for_creation = st.selectbox(
            "Select Node for Creation",
            [node['name'] for node in NODES]
        )

        verify_on_all = st.checkbox("Verify on all nodes after creation", value=True)

        submitted = st.form_submit_button("🚀 Create Asset")

        if submitted:
            if not asset_title:
                st.error("Please provide an asset title!")
            else:
                with st.spinner("Creating asset..."):
                    asset_data = {
                        'data': {
                            'type': asset_type,
                            'title': asset_title,
                            'description': asset_description,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    }

                    metadata = {
                        'creator': creator_name,
                        metadata_key: metadata_value if metadata_value else None
                    }

                    selected_node = next(node for node in NODES if node['name'] == node_for_creation)
                    tx_id, creator_keypair = create_asset_transaction(
                        selected_node['url'],
                        asset_data,
                        metadata
                    )

                    if tx_id:
                        st.markdown(
                            f'<div class="success-box">✓ <b>Asset created successfully!</b><br>Transaction ID: <code>{tx_id}</code></div>',
                            unsafe_allow_html=True)

                        # Store keypair for later transfers
                        st.session_state.keypairs[tx_id] = creator_keypair

                        # Add to transaction history
                        tx_record = {
                            'tx_id': tx_id,
                            'type': 'CREATE',
                            'asset_title': asset_title,
                            'node': node_for_creation,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'success',
                            'creator_key': creator_keypair.public_key[:20] + "..."
                        }
                        st.session_state.transactions.append(tx_record)

                        if verify_on_all:
                            with st.spinner("Verifying on all nodes (15 seconds)..."):
                                time.sleep(15)
                                results = verify_transaction_on_nodes(tx_id, NODES)

                                found_count = sum(1 for r in results.values() if r['found'])

                                st.subheader("Verification Results")
                                col1, col2, col3, col4 = st.columns(4)

                                for i, (node_name, result) in enumerate(results.items()):
                                    with [col1, col2, col3, col4][i]:
                                        if result['found']:
                                            st.success(f"✓ {node_name}")
                                        else:
                                            st.error(f"✗ {node_name}")

                                st.metric("Replication Status", f"{found_count}/4 nodes")
                    else:
                        st.markdown('<div class="error-box">✗ Failed to create asset</div>', unsafe_allow_html=True)

# Page 3: Transfer Asset
elif st.session_state.current_page == "🔄 Transfer Asset":
    st.markdown('<div class="sub-header">Transfer Asset</div>', unsafe_allow_html=True)

    if not st.session_state.transactions:
        st.info("ℹ️ No assets created yet. Create an asset first.")
    else:
        # Get CREATE transactions with stored keypairs
        transferable_txs = [
            tx for tx in st.session_state.transactions
            if tx['type'] == 'CREATE' and tx['tx_id'] in st.session_state.keypairs
        ]

        if not transferable_txs:
            st.warning("⚠️ No transferable assets found.")
        else:
            with st.form("transfer_asset_form"):
                col1, col2 = st.columns(2)

                with col1:
                    # Select transaction to transfer
                    tx_options = {
                        f"{tx['asset_title']} ({tx['tx_id'][:10]}...)": tx['tx_id']
                        for tx in transferable_txs
                    }

                    selected_tx_display = st.selectbox("Select Asset to Transfer", list(tx_options.keys()))
                    transfer_to_name = st.text_input("Transfer To (Name)", placeholder="e.g., Bob")

                with col2:
                    node_for_transfer = st.selectbox(
                        "Select Node for Transfer",
                        [node['name'] for node in NODES]
                    )

                    transfer_note = st.text_area("Transfer Note", placeholder="Optional note")

                verify_transfer = st.checkbox("Verify transfer on all nodes", value=True)

                submitted_transfer = st.form_submit_button("🔄 Transfer Asset")

                if submitted_transfer:
                    selected_tx_id = tx_options[selected_tx_display]

                    # Find the full transaction
                    original_tx = next(
                        tx for tx in st.session_state.transactions
                        if tx['tx_id'] == selected_tx_id
                    )

                    with st.spinner("Transferring asset..."):
                        # Generate keypair for recipient
                        recipient_keypair = generate_keypair()

                        transfer_metadata = {
                            'transfer_to': transfer_to_name,
                            'transfer_note': transfer_note,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        }

                        selected_node = next(node for node in NODES if node['name'] == node_for_transfer)
                        from_keypair = st.session_state.keypairs[original_tx['tx_id']]

                        transfer_tx_id = transfer_asset(
                            selected_node['url'],
                            original_tx['tx_id'],
                            from_keypair,
                            recipient_keypair.public_key,
                            transfer_metadata
                        )

                        if transfer_tx_id:
                            st.markdown(
                                f'<div class="success-box">✓ <b>Asset transferred successfully!</b><br>Transfer TX ID: <code>{transfer_tx_id}</code></div>',
                                unsafe_allow_html=True)

                            # Store new keypair
                            st.session_state.keypairs[transfer_tx_id] = recipient_keypair

                            # Add to transaction history
                            tx_record = {
                                'tx_id': transfer_tx_id,
                                'type': 'TRANSFER',
                                'asset_title': original_tx['asset_title'],
                                'node': node_for_transfer,
                                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'status': 'success',
                                'from': original_tx.get('creator_key', 'Unknown'),
                                'to': recipient_keypair.public_key[:20] + "..."
                            }
                            st.session_state.transactions.append(tx_record)

                            if verify_transfer:
                                with st.spinner("Verifying transfer (15 seconds)..."):
                                    time.sleep(15)
                                    results = verify_transaction_on_nodes(transfer_tx_id, NODES)

                                    found_count = sum(1 for r in results.values() if r['found'])

                                    st.subheader("Verification Results")
                                    col1, col2, col3, col4 = st.columns(4)

                                    for i, (node_name, result) in enumerate(results.items()):
                                        with [col1, col2, col3, col4][i]:
                                            if result['found']:
                                                st.success(f"✓ {node_name}")
                                            else:
                                                st.error(f"✗ {node_name}")

                                    st.metric("Replication Status", f"{found_count}/4 nodes")
                        else:
                            st.markdown('<div class="error-box">✗ Failed to transfer asset</div>',
                                        unsafe_allow_html=True)

# Page 4: Query Transaction
elif st.session_state.current_page == "🔍 Query Transaction":
    st.markdown('<div class="sub-header">Query Transaction</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col1:
        query_tx_id = st.text_input(
            "Transaction ID",
            placeholder="Enter full transaction ID"
        )

    with col2:
        query_node = st.selectbox(
            "Query Node",
            [node['name'] for node in NODES]
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Query Transaction"):
            if not query_tx_id:
                st.error("Please enter a transaction ID")
            else:
                with st.spinner("Querying transaction..."):
                    selected_node = next(node for node in NODES if node['name'] == query_node)
                    tx = get_transaction_details(selected_node['url'], query_tx_id)

                    if tx:
                        st.success(f"✓ Transaction found on {query_node}")

                        st.subheader("Transaction Details")
                        st.write("**Operation:**", tx['operation'])
                        st.write("**ID:**", tx['id'])

                        if 'asset' in tx and 'data' in tx['asset']:
                            st.subheader("Asset Data")
                            st.json(tx['asset']['data'])

                        if 'metadata' in tx and tx['metadata']:
                            st.subheader("Metadata")
                            st.json(tx['metadata'])

                        with st.expander("View Full Transaction JSON"):
                            st.json(tx)
                    else:
                        st.error(f"✗ Transaction not found on {query_node}")

    with col2:
        if st.button("📡 Verify on All Nodes"):
            if not query_tx_id:
                st.error("Please enter a transaction ID")
            else:
                with st.spinner("Verifying on all nodes..."):
                    results = verify_transaction_on_nodes(query_tx_id, NODES)

                    st.subheader("Verification Results")

                    for node_name, result in results.items():
                        if result['found']:
                            st.success(f"✓ {node_name}")
                        else:
                            st.error(f"✗ {node_name}")

                    found_count = sum(1 for r in results.values() if r['found'])
                    st.metric("Found on", f"{found_count}/4 nodes")

    # Recent transactions
    if st.session_state.transactions:
        st.markdown("---")
        st.subheader("Recent Transactions (click to query)")
        for tx in st.session_state.transactions[-5:]:
            if st.button(f"{tx['type']}: {tx['asset_title']} - {tx['tx_id'][:20]}...", key=f"recent_{tx['tx_id']}"):
                st.info(f"Copy this ID: {tx['tx_id']}")

# Page 5: Transaction History
elif st.session_state.current_page == "📜 Transaction History":
    st.markdown('<div class="sub-header">Transaction History</div>', unsafe_allow_html=True)

    if not st.session_state.transactions:
        st.info("ℹ️ No transactions recorded yet.")
    else:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)

        total_txs = len(st.session_state.transactions)
        create_txs = sum(1 for tx in st.session_state.transactions if tx['type'] == 'CREATE')
        transfer_txs = sum(1 for tx in st.session_state.transactions if tx['type'] == 'TRANSFER')
        success_txs = sum(1 for tx in st.session_state.transactions if tx['status'] == 'success')

        with col1:
            st.metric("Total Transactions", total_txs)
        with col2:
            st.metric("CREATE Operations", create_txs)
        with col3:
            st.metric("TRANSFER Operations", transfer_txs)
        with col4:
            st.metric("Successful", success_txs)

        st.markdown("---")

        # Transaction table
        st.subheader("Transaction List")

        df_transactions = pd.DataFrame(st.session_state.transactions)
        df_transactions['tx_id_short'] = df_transactions['tx_id'].apply(lambda x: x[:20] + "...")

        display_columns = ['timestamp', 'type', 'asset_title', 'tx_id_short', 'node', 'status']
        df_display = df_transactions[display_columns]

        st.dataframe(df_display)

        # Export
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            csv = df_transactions.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"bigchaindb_tx_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        with col2:
            json_data = json.dumps(st.session_state.transactions, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"bigchaindb_tx_{time.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem 0;'>
    <p>🔗 <b>BigchainDB Network Dashboard</b></p>
</div>
""", unsafe_allow_html=True)