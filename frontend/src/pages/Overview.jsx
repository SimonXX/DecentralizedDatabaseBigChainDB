import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { checkAllNodes } from '../api/bigchaindb';

export default function Overview({ nodeStatuses, setNodeStatuses, transactions }) {
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const statuses = await checkAllNodes();
      setNodeStatuses(statuses);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (nodeStatuses.length === 0) refresh();
  }, []);

  const onlineCount = nodeStatuses.filter((n) => n.status === 'online').length;
  const successCount = transactions.filter((t) => t.status === 'success').length;
  const successRate = transactions.length > 0 ? ((successCount / transactions.length) * 100).toFixed(1) : '0.0';

  return (
    <>
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 className="page-title">Network Overview</h1>
            <p className="page-description">Monitor the BigchainDB cluster status and activity</p>
          </div>
          <button className="btn btn-secondary" onClick={refresh} disabled={loading}>
            {loading ? <span className="spinner" /> : <RefreshCw size={16} />}
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-title">Total Nodes</div>
          <div className="card-value">4</div>
        </div>
        <div className="card">
          <div className="card-title">Online Nodes</div>
          <div className="card-value" style={{ color: onlineCount === 4 ? 'var(--success)' : 'var(--warning)' }}>
            {onlineCount}
          </div>
        </div>
        <div className="card">
          <div className="card-title">Transactions</div>
          <div className="card-value">{transactions.length}</div>
        </div>
        <div className="card">
          <div className="card-title">Success Rate</div>
          <div className="card-value">{successRate}%</div>
        </div>
      </div>

      <h2 style={{ fontSize: '1.1rem', marginBottom: 16, color: 'var(--text-secondary)' }}>Node Details</h2>
      <div className="grid grid-4" style={{ marginBottom: 32 }}>
        {nodeStatuses.map((node) => (
          <div className={`node-card ${node.status === 'online' ? 'online' : 'offline'}`} key={node.name}>
            <div className="glow" />
            <div className="node-name">
              <span className={`status-dot ${node.status === 'online' ? 'online' : 'offline'}`} />
              {node.name}
            </div>
            <div className="node-detail">
              <span>Status</span>
              <span>{node.status}</span>
            </div>
            <div className="node-detail">
              <span>BigchainDB</span>
              <span style={{ color: node.bigchaindb ? 'var(--success)' : 'var(--error)' }}>
                {node.bigchaindb ? 'OK' : 'DOWN'}
              </span>
            </div>
            <div className="node-detail">
              <span>Tendermint</span>
              <span style={{ color: node.tendermint ? 'var(--success)' : 'var(--error)' }}>
                {node.tendermint ? 'OK' : 'DOWN'}
              </span>
            </div>
            <div className="node-detail">
              <span>Block Height</span>
              <span>{node.blockHeight}</span>
            </div>
          </div>
        ))}
      </div>

      <h2 style={{ fontSize: '1.1rem', marginBottom: 16, color: 'var(--text-secondary)' }}>Recent Activity</h2>
      <div className="card">
        {transactions.length === 0 ? (
          <div className="empty-state">
            <p>No transactions yet. Create an asset to get started.</p>
          </div>
        ) : (
          transactions
            .slice(-5)
            .reverse()
            .map((tx) => (
              <div className="tx-item" key={tx.txId}>
                <span className={`tx-type ${tx.type.toLowerCase()}`}>{tx.type}</span>
                <div className="tx-info">
                  <div className="tx-title">{tx.assetTitle}</div>
                  <div className="tx-id">{tx.txId.slice(0, 24)}...</div>
                </div>
                <div className="tx-meta">
                  <div>{tx.node}</div>
                  <div>{tx.timestamp}</div>
                </div>
              </div>
            ))
        )}
      </div>
    </>
  );
}
