import { Download, Trash2 } from 'lucide-react';

export default function History({ transactions, clearHistory }) {
  const createCount = transactions.filter((t) => t.type === 'CREATE').length;
  const transferCount = transactions.filter((t) => t.type === 'TRANSFER').length;
  const successCount = transactions.filter((t) => t.status === 'success').length;

  const downloadCSV = () => {
    const headers = ['timestamp', 'type', 'assetTitle', 'txId', 'node', 'status'];
    const rows = transactions.map((tx) => headers.map((h) => tx[h] || '').join(','));
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bigchaindb_tx_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(transactions, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bigchaindb_tx_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 className="page-title">Transaction History</h1>
            <p className="page-description">View and export all recorded transactions</p>
          </div>
          {transactions.length > 0 && (
            <button className="btn btn-danger" onClick={clearHistory}>
              <Trash2 size={16} /> Clear History
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-title">Total</div>
          <div className="card-value">{transactions.length}</div>
        </div>
        <div className="card">
          <div className="card-title">CREATE</div>
          <div className="card-value" style={{ color: 'var(--info)' }}>{createCount}</div>
        </div>
        <div className="card">
          <div className="card-title">TRANSFER</div>
          <div className="card-value" style={{ color: 'var(--warning)' }}>{transferCount}</div>
        </div>
        <div className="card">
          <div className="card-title">Successful</div>
          <div className="card-value" style={{ color: 'var(--success)' }}>{successCount}</div>
        </div>
      </div>

      {transactions.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p>No transactions recorded yet.</p>
          </div>
        </div>
      ) : (
        <>
          <div className="table-container" style={{ marginBottom: 24 }}>
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Type</th>
                  <th>Asset</th>
                  <th>Transaction ID</th>
                  <th>Node</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {[...transactions].reverse().map((tx) => (
                  <tr key={tx.txId}>
                    <td className="mono">{tx.timestamp}</td>
                    <td>
                      <span className={`tx-type ${tx.type.toLowerCase()}`}>{tx.type}</span>
                    </td>
                    <td>{tx.assetTitle}</td>
                    <td className="mono">{tx.txId.slice(0, 20)}...</td>
                    <td>{tx.node}</td>
                    <td>
                      <span className={`badge ${tx.status === 'success' ? 'badge-success' : 'badge-error'}`}>
                        {tx.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button className="btn btn-secondary" onClick={downloadCSV}>
              <Download size={16} /> Download CSV
            </button>
            <button className="btn btn-secondary" onClick={downloadJSON}>
              <Download size={16} /> Download JSON
            </button>
          </div>
        </>
      )}
    </>
  );
}
