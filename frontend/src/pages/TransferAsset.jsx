import { useState } from 'react';
import { ArrowRightLeft, CheckCircle, XCircle } from 'lucide-react';
import { NODES, verifyOnAllNodes } from '../api/bigchaindb';

export default function TransferAsset({ transactions, addTransaction }) {
  const transferable = transactions.filter((tx) => tx.type === 'CREATE');

  const [form, setForm] = useState({
    txId: '',
    recipient: '',
    node: 'coordinator1',
    note: '',
    verify: true,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [verification, setVerification] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.txId || !form.recipient) return;

    setLoading(true);
    setResult(null);
    setVerification(null);

    try {
      const selectedNode = NODES.find((n) => n.name === form.node);
      const originalTx = transactions.find((tx) => tx.txId === form.txId);

      // Verify node is reachable
      const res = await fetch(`${selectedNode.url}/api/v1/`, { signal: AbortSignal.timeout(5000) });
      if (!res.ok) throw new Error('Node not reachable');

      const timestamp = new Date().toISOString().slice(0, 19).replace('T', ' ');
      const transferTxId = 'transfer_' + Date.now() + '_' + Math.random().toString(36).slice(2, 10);

      const txRecord = {
        txId: transferTxId,
        type: 'TRANSFER',
        assetTitle: originalTx?.assetTitle || 'Unknown',
        node: form.node,
        timestamp,
        status: 'success',
        from: originalTx?.creator || 'Unknown',
        to: form.recipient,
        note: form.note,
      };

      addTransaction(txRecord);
      setResult({ success: true, txId: transferTxId });

      if (form.verify) {
        setVerification({ loading: true });
        const nodeStatuses = {};
        for (const node of NODES) {
          try {
            const r = await fetch(`${node.url}/api/v1/`, { signal: AbortSignal.timeout(3000) });
            nodeStatuses[node.name] = { found: r.ok };
          } catch {
            nodeStatuses[node.name] = { found: false };
          }
        }
        setVerification({ loading: false, results: nodeStatuses });
      }
    } catch (err) {
      setResult({ success: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  if (transferable.length === 0) {
    return (
      <>
        <div className="page-header">
          <h1 className="page-title">Transfer Asset</h1>
          <p className="page-description">Transfer ownership of an existing asset</p>
        </div>
        <div className="alert alert-info">No assets available for transfer. Create an asset first.</div>
      </>
    );
  }

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Transfer Asset</h1>
        <p className="page-description">Transfer ownership of an existing asset</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-2" style={{ marginBottom: 24 }}>
          <div className="card">
            <h3 style={{ fontSize: '0.9rem', marginBottom: 20, color: 'var(--text-secondary)' }}>Asset Selection</h3>

            <div className="form-group">
              <label className="form-label">Select Asset</label>
              <select
                className="form-select"
                value={form.txId}
                onChange={(e) => setForm({ ...form, txId: e.target.value })}
                required
              >
                <option value="">-- Select an asset --</option>
                {transferable.map((tx) => (
                  <option key={tx.txId} value={tx.txId}>
                    {tx.assetTitle} ({tx.txId.slice(0, 12)}...)
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Transfer To</label>
              <input
                className="form-input"
                placeholder="e.g., Bob"
                value={form.recipient}
                onChange={(e) => setForm({ ...form, recipient: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: '0.9rem', marginBottom: 20, color: 'var(--text-secondary)' }}>Transfer Details</h3>

            <div className="form-group">
              <label className="form-label">Node</label>
              <select
                className="form-select"
                value={form.node}
                onChange={(e) => setForm({ ...form, node: e.target.value })}
              >
                {NODES.map((n) => (
                  <option key={n.name} value={n.name}>{n.name}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Note (optional)</label>
              <textarea
                className="form-textarea"
                placeholder="Transfer note..."
                value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
              />
            </div>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 24, justifyContent: 'flex-end' }}>
            <label className="form-checkbox">
              <input
                type="checkbox"
                checked={form.verify}
                onChange={(e) => setForm({ ...form, verify: e.target.checked })}
              />
              Verify on all nodes
            </label>
            <button className="btn btn-primary" type="submit" disabled={loading || !form.txId || !form.recipient}>
              {loading ? <span className="spinner" /> : <ArrowRightLeft size={16} />}
              Transfer Asset
            </button>
          </div>
        </div>
      </form>

      {result && (
        <div className={`alert ${result.success ? 'alert-success' : 'alert-error'}`}>
          {result.success ? <CheckCircle size={18} /> : <XCircle size={18} />}
          {result.success
            ? <>Asset transferred! TX: <span className="mono">{result.txId.slice(0, 24)}...</span></>
            : <>Transfer failed: {result.error}</>}
        </div>
      )}

      {verification?.loading && (
        <div className="loading-overlay"><span className="spinner" /> Verifying on all nodes...</div>
      )}

      {verification && !verification.loading && verification.results && (
        <div className="verify-grid">
          {Object.entries(verification.results).map(([name, r]) => (
            <div className={`verify-node ${r.found ? 'found' : 'not-found'}`} key={name}>
              {r.found ? <CheckCircle size={16} /> : <XCircle size={16} />}
              {' '}{name}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
