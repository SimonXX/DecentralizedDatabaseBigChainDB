import { useState } from 'react';
import { Search, CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { NODES, getTransaction, verifyOnAllNodes } from '../api/bigchaindb';

export default function QueryTransaction({ transactions }) {
  const [txId, setTxId] = useState('');
  const [queryNode, setQueryNode] = useState('coordinator1');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [verification, setVerification] = useState(null);
  const [showJson, setShowJson] = useState(false);

  const handleQuery = async () => {
    if (!txId) return;
    setLoading(true);
    setResult(null);
    setVerification(null);

    try {
      const node = NODES.find((n) => n.name === queryNode);
      const tx = await getTransaction(node.url, txId);

      if (tx) {
        setResult({ found: true, transaction: tx, node: queryNode });
      } else {
        setResult({ found: false, node: queryNode });
      }
    } catch (err) {
      setResult({ found: false, node: queryNode, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyAll = async () => {
    if (!txId) return;
    setVerification({ loading: true });

    try {
      const results = await verifyOnAllNodes(txId);
      setVerification({ loading: false, results });
    } catch {
      setVerification({ loading: false, results: {} });
    }
  };

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Query Transaction</h1>
        <p className="page-description">Look up and verify transactions across the network</p>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="grid grid-2" style={{ marginBottom: 20 }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Transaction ID</label>
            <input
              className="form-input"
              placeholder="Enter full transaction ID"
              value={txId}
              onChange={(e) => setTxId(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Query Node</label>
            <select className="form-select" value={queryNode} onChange={(e) => setQueryNode(e.target.value)}>
              {NODES.map((n) => (
                <option key={n.name} value={n.name}>{n.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-primary" onClick={handleQuery} disabled={loading || !txId}>
            {loading ? <span className="spinner" /> : <Search size={16} />}
            Query
          </button>
          <button className="btn btn-secondary" onClick={handleVerifyAll} disabled={!txId}>
            Verify on All Nodes
          </button>
        </div>
      </div>

      {result && (
        <div style={{ marginBottom: 24 }}>
          {result.found ? (
            <>
              <div className="alert alert-success">
                <CheckCircle size={18} /> Transaction found on {result.node}
              </div>

              <div className="card" style={{ marginBottom: 16 }}>
                <h3 style={{ fontSize: '0.9rem', marginBottom: 16, color: 'var(--text-secondary)' }}>
                  Transaction Details
                </h3>
                <div className="node-detail">
                  <span>Operation</span>
                  <span>{result.transaction.operation}</span>
                </div>
                <div className="node-detail">
                  <span>ID</span>
                  <span className="mono">{result.transaction.id}</span>
                </div>

                {result.transaction.asset?.data && (
                  <>
                    <hr className="divider" />
                    <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 8 }}>Asset Data</h4>
                    <div className="json-viewer">{JSON.stringify(result.transaction.asset.data, null, 2)}</div>
                  </>
                )}

                {result.transaction.metadata && (
                  <>
                    <hr className="divider" />
                    <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 8 }}>Metadata</h4>
                    <div className="json-viewer">{JSON.stringify(result.transaction.metadata, null, 2)}</div>
                  </>
                )}
              </div>

              <div
                className="collapsible-header"
                onClick={() => setShowJson(!showJson)}
              >
                Full Transaction JSON
                {showJson ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
              {showJson && (
                <div className="collapsible-body">
                  <div className="json-viewer">{JSON.stringify(result.transaction, null, 2)}</div>
                </div>
              )}
            </>
          ) : (
            <div className="alert alert-error">
              <XCircle size={18} /> Transaction not found on {result.node}
              {result.error && ` (${result.error})`}
            </div>
          )}
        </div>
      )}

      {verification?.loading && (
        <div className="loading-overlay"><span className="spinner" /> Verifying on all nodes...</div>
      )}

      {verification && !verification.loading && verification.results && (
        <>
          <h3 style={{ fontSize: '0.9rem', marginBottom: 8, color: 'var(--text-secondary)' }}>Verification Results</h3>
          <div className="verify-grid">
            {Object.entries(verification.results).map(([name, r]) => (
              <div className={`verify-node ${r.found ? 'found' : 'not-found'}`} key={name}>
                {r.found ? <CheckCircle size={16} /> : <XCircle size={16} />}
                {' '}{name}
              </div>
            ))}
          </div>
        </>
      )}

      {transactions.length > 0 && (
        <>
          <hr className="divider" />
          <h3 style={{ fontSize: '0.9rem', marginBottom: 12, color: 'var(--text-secondary)' }}>
            Recent Transactions (click to query)
          </h3>
          <div className="card" style={{ padding: 0 }}>
            {transactions.slice(-5).reverse().map((tx) => (
              <div
                className="tx-item"
                key={tx.txId}
                onClick={() => setTxId(tx.txId)}
                style={{ cursor: 'pointer' }}
              >
                <span className={`tx-type ${tx.type.toLowerCase()}`}>{tx.type}</span>
                <div className="tx-info">
                  <div className="tx-title">{tx.assetTitle}</div>
                  <div className="tx-id">{tx.txId.slice(0, 24)}...</div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  );
}
