// When running inside Docker (nginx), use relative proxy paths.
// When running locally with `npm run dev`, use direct localhost ports.
const isDocker = import.meta.env.VITE_DOCKER === 'true';

const NODES = [
  {
    name: 'coordinator1',
    url: import.meta.env.VITE_NODE1_URL || (isDocker ? '/api/node1' : 'http://localhost:9984'),
    tendermint: import.meta.env.VITE_NODE1_TM || (isDocker ? '/tm/node1' : 'http://localhost:26657'),
  },
  {
    name: 'member2',
    url: import.meta.env.VITE_NODE2_URL || (isDocker ? '/api/node2' : 'http://localhost:9986'),
    tendermint: import.meta.env.VITE_NODE2_TM || (isDocker ? '/tm/node2' : 'http://localhost:26658'),
  },
  {
    name: 'member3',
    url: import.meta.env.VITE_NODE3_URL || (isDocker ? '/api/node3' : 'http://localhost:9988'),
    tendermint: import.meta.env.VITE_NODE3_TM || (isDocker ? '/tm/node3' : 'http://localhost:26659'),
  },
  {
    name: 'member4',
    url: import.meta.env.VITE_NODE4_URL || (isDocker ? '/api/node4' : 'http://localhost:9990'),
    tendermint: import.meta.env.VITE_NODE4_TM || (isDocker ? '/tm/node4' : 'http://localhost:26660'),
  },
];

export { NODES };

const TIMEOUT = 30000;

export async function checkNodeStatus(node) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${node.url}/api/v1/`, { signal: controller.signal });
    clearTimeout(timeoutId);
    const bigchaindbOk = response.ok;

    let tendermintOk = false;
    let blockHeight = 'N/A';

    try {
      const tmController = new AbortController();
      const tmTimeoutId = setTimeout(() => tmController.abort(), 5000);
      const tmResponse = await fetch(`${node.tendermint}/status`, { signal: tmController.signal });
      clearTimeout(tmTimeoutId);
      tendermintOk = tmResponse.ok;
      if (tendermintOk) {
        const tmData = await tmResponse.json();
        blockHeight = tmData.result?.sync_info?.latest_block_height || 'N/A';
      }
    } catch {
      tendermintOk = false;
    }

    return {
      name: node.name,
      url: node.url,
      status: bigchaindbOk ? 'online' : 'offline',
      bigchaindb: bigchaindbOk,
      tendermint: tendermintOk,
      blockHeight,
    };
  } catch {
    return {
      name: node.name,
      url: node.url,
      status: 'unreachable',
      bigchaindb: false,
      tendermint: false,
      blockHeight: 'N/A',
    };
  }
}

export async function checkAllNodes() {
  return Promise.all(NODES.map(checkNodeStatus));
}

export async function createAsset(nodeUrl, assetData, metadata) {
  const response = await fetch(`${nodeUrl}/api/v1/transactions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ asset: assetData, metadata }),
    signal: AbortSignal.timeout(TIMEOUT),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export async function getTransaction(nodeUrl, txId) {
  const response = await fetch(`${nodeUrl}/api/v1/transactions/${txId}`, {
    signal: AbortSignal.timeout(TIMEOUT),
  });

  if (!response.ok) return null;
  return response.json();
}

export async function verifyOnAllNodes(txId) {
  const results = {};
  await Promise.all(
    NODES.map(async (node) => {
      try {
        const tx = await getTransaction(node.url, txId);
        results[node.name] = { found: !!tx, transaction: tx };
      } catch {
        results[node.name] = { found: false };
      }
    })
  );
  return results;
}

export async function searchAssets(nodeUrl, query) {
  const response = await fetch(
    `${nodeUrl}/api/v1/assets/?search=${encodeURIComponent(query)}`,
    { signal: AbortSignal.timeout(TIMEOUT) }
  );
  if (!response.ok) return [];
  return response.json();
}
