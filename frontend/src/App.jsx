import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import CreateAsset from './pages/CreateAsset';
import TransferAsset from './pages/TransferAsset';
import QueryTransaction from './pages/QueryTransaction';
import History from './pages/History';
import { checkAllNodes } from './api/bigchaindb';

function App() {
  const [nodeStatuses, setNodeStatuses] = useState([]);
  const [transactions, setTransactions] = useState(() => {
    const saved = localStorage.getItem('bdb_transactions');
    return saved ? JSON.parse(saved) : [];
  });
  const [keypairs, setKeypairs] = useState({});

  useEffect(() => {
    localStorage.setItem('bdb_transactions', JSON.stringify(transactions));
  }, [transactions]);

  useEffect(() => {
    checkAllNodes().then(setNodeStatuses).catch(() => {});
    const interval = setInterval(() => {
      checkAllNodes().then(setNodeStatuses).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const addTransaction = (tx) => {
    setTransactions((prev) => [...prev, tx]);
  };

  const storeKeypair = (txId, keypair) => {
    setKeypairs((prev) => ({ ...prev, [txId]: keypair }));
  };

  const clearHistory = () => {
    setTransactions([]);
    setKeypairs({});
  };

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar nodeStatuses={nodeStatuses} />
        <main className="main-content">
          <Routes>
            <Route
              path="/"
              element={
                <Overview
                  nodeStatuses={nodeStatuses}
                  setNodeStatuses={setNodeStatuses}
                  transactions={transactions}
                />
              }
            />
            <Route
              path="/create"
              element={<CreateAsset addTransaction={addTransaction} storeKeypair={storeKeypair} />}
            />
            <Route
              path="/transfer"
              element={<TransferAsset transactions={transactions} addTransaction={addTransaction} />}
            />
            <Route
              path="/query"
              element={<QueryTransaction transactions={transactions} />}
            />
            <Route
              path="/history"
              element={<History transactions={transactions} clearHistory={clearHistory} />}
            />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
