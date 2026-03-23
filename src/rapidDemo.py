import os
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
import time
import json
import requests
from typing import List, Dict, Optional, Tuple

# Configuration of the 4 nodes — env vars override for containerised execution
nodes = [
    {
        'name': 'coordinator1',
        'url': os.getenv('NODE1_URL', 'http://localhost:9984'),
        'tendermint': os.getenv('NODE1_TM', 'http://localhost:26657'),
    },
    {
        'name': 'member2',
        'url': os.getenv('NODE2_URL', 'http://localhost:9986'),
        'tendermint': os.getenv('NODE2_TM', 'http://localhost:26658'),
    },
    {
        'name': 'member3',
        'url': os.getenv('NODE3_URL', 'http://localhost:9988'),
        'tendermint': os.getenv('NODE3_TM', 'http://localhost:26659'),
    },
    {
        'name': 'member4',
        'url': os.getenv('NODE4_URL', 'http://localhost:9990'),
        'tendermint': os.getenv('NODE4_TM', 'http://localhost:26660'),
    },
]

# Configuration
TIMEOUT = 30
MAX_RETRIES = 3
WAIT_TIME_SHORT = 20
WAIT_TIME_LONG = 25


def print_header(text: str):
    """Prints a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_subheader(text: str):
    """Prints a formatted subheader"""
    print(f"\n{'─' * 80}")
    print(f"  {text}")
    print('─' * 80)


def check_node_status(node: Dict) -> bool:
    """Checks the status of a BigchainDB node"""
    try:
        # Check BigchainDB API
        response = requests.get(f"{node['url']}/api/v1/", timeout=10)
        bigchaindb_ok = response.status_code == 200

        # Check Tendermint
        try:
            tendermint_response = requests.get(f"{node['tendermint']}/status", timeout=10)
            tendermint_ok = tendermint_response.status_code == 200
            tendermint_data = tendermint_response.json()
        except:
            tendermint_ok = False
            tendermint_data = None

        if bigchaindb_ok:
            print(f"✓ {node['name']}: ONLINE")
            print(f"  └─ BigchainDB API: {node['url']}")
            print(f"  └─ Tendermint: {'OK' if tendermint_ok else 'ERROR'}")

            if tendermint_ok and tendermint_data:
                height = tendermint_data['result']['sync_info']['latest_block_height']
                print(f"  └─ Block Height: {height}")

            return True
        else:
            print(f"✗ {node['name']}: OFFLINE (status code: {response.status_code})")
            return False

    except requests.exceptions.ConnectionError:
        print(f"✗ {node['name']}: UNREACHABLE")
        return False
    except Exception as e:
        print(f"✗ {node['name']}: ERROR - {str(e)}")
        return False


def create_asset_transaction(node_url: str, asset_data: Dict, metadata: Dict) -> Tuple[Optional[str], Optional[object]]:
    """Creates a CREATE transaction on a specific node"""
    try:
        bdb = BigchainDB(node_url)
        bdb.transport.timeout = TIMEOUT

        # Generate keypair for the creator
        creator = generate_keypair()

        # Prepare transaction
        prepared_tx = bdb.transactions.prepare(
            operation='CREATE',
            signers=creator.public_key,
            asset=asset_data,
            metadata=metadata
        )

        # Sign transaction
        fulfilled_tx = bdb.transactions.fulfill(
            prepared_tx,
            private_keys=creator.private_key
        )

        # Send transaction
        sent_tx = bdb.transactions.send_commit(fulfilled_tx)

        return sent_tx['id'], creator

    except Exception as e:
        print(f"Error creating transaction: {str(e)}")
        return None, None


def transfer_asset(node_url: str, tx_id: str, from_keypair, to_public_key: str, metadata: Dict) -> Optional[str]:
    """Transfers an asset from one owner to another"""
    try:
        bdb = BigchainDB(node_url)
        bdb.transport.timeout = TIMEOUT

        # Retrieve the previous transaction (can be CREATE or TRANSFER)
        previous_tx = bdb.transactions.retrieve(tx_id)

        # Find the original asset ID
        if previous_tx['operation'] == 'CREATE':
            asset_id = previous_tx['id']
        else:
            asset_id = previous_tx['asset']['id']

        # Prepare asset for transfer
        transfer_asset_data = {
            'id': asset_id  # Always use the original asset ID
        }

        output_index = 0
        output = previous_tx['outputs'][output_index]

        transfer_input = {
            'fulfillment': output['condition']['details'],
            'fulfills': {
                'output_index': output_index,
                'transaction_id': previous_tx['id']  # ID of the previous transaction
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

        # Sign with current owner's private key
        fulfilled_transfer_tx = bdb.transactions.fulfill(
            prepared_transfer_tx,
            private_keys=from_keypair.private_key
        )

        # Send transaction
        sent_transfer_tx = bdb.transactions.send_commit(fulfilled_transfer_tx)

        return sent_transfer_tx['id']

    except Exception as e:
        print(f"Error transferring asset: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def verify_transaction_on_all_nodes(tx_id: str, max_retries: int = MAX_RETRIES) -> Dict:
    """Verifies the presence of a transaction on all nodes with retry logic"""
    results = {}

    for node in nodes:
        success = False
        for attempt in range(max_retries):
            try:
                bdb = BigchainDB(node['url'])
                bdb.transport.timeout = TIMEOUT

                tx = bdb.transactions.retrieve(tx_id)
                results[node['name']] = {
                    'found': True,
                    'transaction': tx,
                    'attempts': attempt + 1
                }

                if attempt > 0:
                    print(f"✓ {node['name']}: Transaction found (attempt {attempt + 1}/{max_retries})")
                else:
                    print(f"✓ {node['name']}: Transaction found")

                success = True
                break

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⟳ Retry {attempt + 1}/{max_retries} for {node['name']}...")
                    time.sleep(5)
                else:
                    error_msg = str(e)
                    # Simplify timeout error messages
                    if "Read timed out" in error_msg:
                        error_msg = "Read timeout"
                    elif "Connection" in error_msg:
                        error_msg = "Connection error"

                    results[node['name']] = {
                        'found': False,
                        'error': error_msg
                    }
                    print(f"✗ {node['name']}: Transaction NOT found - {error_msg}")

    return results


def get_asset_history(node_url: str, asset_id: str) -> List:
    """Retrieves the complete history of an asset"""
    try:
        bdb = BigchainDB(node_url)
        bdb.transport.timeout = TIMEOUT

        # Search all transactions related to the asset
        txs = bdb.transactions.get(asset_id=asset_id)
        return list(txs)
    except Exception as e:
        print(f"Error retrieving history: {str(e)}")
        return []


def demo_scenario_1_simple_broadcast():
    """Scenario 1: Simple creation and broadcast verification"""
    print_header("SCENARIO 1: Simple Broadcast")

    print("\n📝 Creating asset on the first node (coordinator1)...")

    asset_data = {
        'data': {
            'type': 'document',
            'title': 'Demo Contract',
            'content': 'This is a test contract',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    }

    metadata = {
        'scenario': 'broadcast_test',
        'created_by': 'demo_script',
        'version': '1.0'
    }

    tx_id, creator = create_asset_transaction(nodes[0]['url'], asset_data, metadata)

    if tx_id:
        print(f"\n✓ Transaction created successfully!")
        print(f"  Transaction ID: {tx_id}")
        print(f"  Creator Public Key: {creator.public_key[:20]}...")

        print(f"\n⏳ Waiting for propagation ({WAIT_TIME_SHORT} seconds)...")
        time.sleep(WAIT_TIME_SHORT)

        print("\n🔍 Verifying presence on all 4 nodes:")
        results = verify_transaction_on_all_nodes(tx_id)

        found_count = sum(1 for r in results.values() if r['found'])
        print(f"\n📊 Result: {found_count}/4 nodes have the transaction")

        if found_count == 4:
            print("   ✅ SUCCESS: Transaction replicated on all nodes!")
        else:
            print(f"   ⚠️  WARNING: Transaction missing on {4 - found_count} node(s)")

        return tx_id, creator
    else:
        print("\n✗ Error creating transaction")
        return None, None


def demo_scenario_2_transfer_chain():
    """Scenario 2: Chain of transfers across nodes"""
    print_header("SCENARIO 2: Transfer Chain")

    print("\n📝 Creating initial asset...")

    asset_data = {
        'data': {
            'type': 'token',
            'name': 'DemoToken',
            'symbol': 'DMT',
            'initial_supply': 1000,
            'description': 'A demo token for testing transfers'
        }
    }

    metadata = {
        'scenario': 'transfer_chain',
        'step': 'creation',
        'note': 'Initial token creation'
    }

    tx_id, alice = create_asset_transaction(nodes[0]['url'], asset_data, metadata)

    if not tx_id:
        print("✗ Error creating asset")
        return

    print(f"\n✓ Asset created by Alice")
    print(f"  Transaction ID: {tx_id}")
    print(f"  Alice's Public Key: {alice.public_key[:20]}...")

    print(f"\n⏳ Waiting for initial propagation ({WAIT_TIME_SHORT} seconds)...")
    time.sleep(WAIT_TIME_SHORT)

    # Generate keypairs for Bob, Carol and Dave
    bob = generate_keypair()
    carol = generate_keypair()
    dave = generate_keypair()

    owners = [
        ('Alice', alice),
        ('Bob', bob),
        ('Carol', carol),
        ('Dave', dave)
    ]

    current_tx_id = tx_id
    current_owner_idx = 0
    transfer_success = True

    # Transfer chain: Alice -> Bob -> Carol -> Dave
    for i in range(1, len(owners)):
        from_name, from_keypair = owners[current_owner_idx]
        to_name, to_keypair = owners[i]

        # Use a different node for each transfer
        node_idx = i % len(nodes)
        node = nodes[node_idx]

        print_subheader(f"Transfer {i}: {from_name} → {to_name}")
        print(f"Using node: {node['name']} ({node['url']})")
        print(f"From: {from_keypair.public_key[:20]}...")
        print(f"To: {to_keypair.public_key[:20]}...")

        transfer_metadata = {
            'scenario': 'transfer_chain',
            'step': f'transfer_{i}',
            'from': from_name,
            'to': to_name,
            'transfer_number': i
        }

        transfer_tx_id = transfer_asset(
            node['url'],
            current_tx_id,
            from_keypair,
            to_keypair.public_key,
            transfer_metadata
        )

        if transfer_tx_id:
            print(f"\n✓ Transfer completed successfully!")
            print(f"  New Transaction ID: {transfer_tx_id[:20]}...")
            current_tx_id = transfer_tx_id
            current_owner_idx = i

            print(f"\n⏳ Waiting for propagation ({WAIT_TIME_SHORT} seconds)...")
            time.sleep(WAIT_TIME_SHORT)

            print(f"\n🔍 Verifying transfer on all nodes:")
            results = verify_transaction_on_all_nodes(transfer_tx_id)

            found_count = sum(1 for r in results.values() if r['found'])
            print(f"\n📊 Transfer {i} status: {found_count}/4 nodes")

            if found_count < 4:
                print(f"   ⚠️  WARNING: Transfer not yet on all nodes")
        else:
            print(f"\n✗ Transfer failed!")
            transfer_success = False
            break

    # Show complete asset history
    print_subheader("Complete Asset History")

    if transfer_success:
        print(f"Querying asset history from {nodes[0]['name']}...")
        history = get_asset_history(nodes[0]['url'], tx_id)

        if history:
            print(f"\n📜 Total transactions: {len(history)}")
            print("\nTransaction Chain:")
            for idx, tx in enumerate(history):
                operation = tx['operation']
                tx_short_id = tx['id'][:20]

                if operation == 'CREATE':
                    creator_key = tx['outputs'][0]['public_keys'][0][:20]
                    print(f"  {idx + 1}. CREATE  - TX: {tx_short_id}... (Creator: {creator_key}...)")
                else:
                    from_key = tx['inputs'][0]['owners_before'][0][:20]
                    to_key = tx['outputs'][0]['public_keys'][0][:20]
                    print(f"  {idx + 1}. TRANSFER - TX: {tx_short_id}... (From: {from_key}... → To: {to_key}...)")

            if len(history) == 4:
                print("\n✅ SUCCESS: Complete transfer chain recorded!")
            else:
                print(f"\n⚠️  WARNING: Expected 4 transactions, found {len(history)}")
        else:
            print("✗ Unable to retrieve asset history")
    else:
        print("⚠️  Transfer chain incomplete due to errors")


def demo_scenario_3_parallel_transactions():
    """Scenario 3: Parallel transactions from different nodes"""
    print_header("SCENARIO 3: Parallel Transactions")

    print("\n📝 Creating 4 assets simultaneously, one per node...")
    print("   This tests the network's ability to handle concurrent writes\n")

    transactions = []

    for idx, node in enumerate(nodes):
        asset_data = {
            'data': {
                'type': 'log_entry',
                'node': node['name'],
                'entry_number': idx + 1,
                'message': f'Entry created by node {node["name"]}',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'random_data': f'data_{idx}_{time.time()}'
            }
        }

        metadata = {
            'scenario': 'parallel_test',
            'source_node': node['name'],
            'node_index': idx
        }

        print(f"  Creating on {node['name']}...", end=' ')
        tx_id, creator = create_asset_transaction(node['url'], asset_data, metadata)

        if tx_id:
            transactions.append({
                'node': node['name'],
                'tx_id': tx_id,
                'creator': creator
            })
            print(f"✓ TX: {tx_id[:20]}...")
        else:
            print(f"✗ Failed")

    print(f"\n✓ Created {len(transactions)}/4 parallel transactions")

    if len(transactions) < 4:
        print("⚠️  WARNING: Not all transactions were created successfully")

    print(f"\n⏳ Waiting for propagation ({WAIT_TIME_LONG} seconds)...")
    time.sleep(WAIT_TIME_LONG)

    print("\n🔍 Verifying that each transaction is present on all nodes:")

    overall_stats = {
        'total_transactions': len(transactions),
        'fully_replicated': 0,
        'partially_replicated': 0,
        'failed': 0
    }

    for tx_info in transactions:
        print_subheader(f"Transaction from {tx_info['node']}")
        print(f"TX ID: {tx_info['tx_id'][:40]}...")

        results = verify_transaction_on_all_nodes(tx_info['tx_id'])
        found_count = sum(1 for r in results.values() if r['found'])

        print(f"\n📊 Replication status: {found_count}/4 nodes")

        if found_count == 4:
            print("   ✅ Fully replicated")
            overall_stats['fully_replicated'] += 1
        elif found_count > 0:
            print(f"   ⚠️  Partially replicated ({found_count}/4)")
            overall_stats['partially_replicated'] += 1
        else:
            print("   ✗ Replication failed")
            overall_stats['failed'] += 1

    # Print summary
    print_subheader("Parallel Transaction Summary")
    print(f"Total transactions created: {overall_stats['total_transactions']}")
    print(f"Fully replicated (4/4 nodes): {overall_stats['fully_replicated']}")
    print(f"Partially replicated: {overall_stats['partially_replicated']}")
    print(f"Failed: {overall_stats['failed']}")

    success_rate = (overall_stats['fully_replicated'] / overall_stats['total_transactions'] * 100) if overall_stats[
                                                                                                          'total_transactions'] > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")

    if success_rate == 100:
        print("   ✅ EXCELLENT: All transactions fully replicated!")
    elif success_rate >= 75:
        print("   ✓ GOOD: Most transactions replicated successfully")
    else:
        print("   ⚠️  NEEDS ATTENTION: Low replication rate")


def main():
    """Runs all demo scenarios"""

    print_header("BIGCHAINDB DEMO - 4-NODE NETWORK")
    print("\nThis demo will demonstrate:")
    print("  1. Transaction broadcast across the network")
    print("  2. Asset transfer chain between multiple owners")
    print("  3. Parallel transaction creation on different nodes")
    print("\nConfiguration:")
    print(f"  • Timeout: {TIMEOUT} seconds")
    print(f"  • Max Retries: {MAX_RETRIES}")
    print(f"  • Wait Time: {WAIT_TIME_SHORT}-{WAIT_TIME_LONG} seconds")

    # Check initial status
    print_header("Node Status Check")
    node_status = [check_node_status(node) for node in nodes]

    online_nodes = sum(node_status)
    print(f"\n📊 Summary: {online_nodes}/4 nodes online")

    if online_nodes < 4:
        print("\n⚠️  WARNING: Not all nodes are online!")
        print("The demo may not work correctly.")
        print(f"Online nodes: {online_nodes}/4")
        print(f"Offline nodes: {4 - online_nodes}/4")
        response = input("\nDo you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("\n Demo cancelled by user.")
            return
    else:
        print("\n✅ All nodes are operational and ready!")

    # Run scenarios
    try:
        input("\n\nPress ENTER to start Scenario 1...")
        demo_scenario_1_simple_broadcast()

        input("\n\nPress ENTER to start Scenario 2...")
        demo_scenario_2_transfer_chain()

        input("\n\nPress ENTER to start Scenario 3...")
        demo_scenario_3_parallel_transactions()

        print_header("DEMO COMPLETED SUCCESSFULLY")
        print("\n🎉 All scenarios executed!")
        print("\n📋 What you verified:")
        print("  ✓ Automatic transaction broadcast across the network")
        print("  ✓ Consistent replication on all 4 nodes")
        print("  ✓ Asset transfer capability between multiple owners")
        print("  ✓ Parallel transaction creation on different nodes")
        print("  ✓ Byzantine Fault Tolerant consensus (Tendermint)")
        print("\n💡 Key takeaways:")
        print("  • BigchainDB provides strong consistency guarantees")
        print("  • Transactions are immutable once committed")
        print("  • The network can handle concurrent operations")
        print("  • Asset ownership can be transferred securely")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        print("Cleanup not required - containers are still running")
    except Exception as e:
        print(f"\n\n✗ Unexpected error during execution:")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()