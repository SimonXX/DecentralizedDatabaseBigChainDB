import { NavLink } from 'react-router-dom';
import { Activity, PlusCircle, ArrowRightLeft, Search, Clock } from 'lucide-react';

export default function Sidebar({ nodeStatuses }) {
  const onlineCount = nodeStatuses.filter((n) => n.status === 'online').length;

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">BigchainDB</div>
      <div className="sidebar-subtitle">Network Dashboard</div>

      <nav className="nav-section">
        <div className="nav-section-title">Navigation</div>
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Activity /> Overview
        </NavLink>
        <NavLink to="/create" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <PlusCircle /> Create Asset
        </NavLink>
        <NavLink to="/transfer" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <ArrowRightLeft /> Transfer Asset
        </NavLink>
        <NavLink to="/query" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Search /> Query Transaction
        </NavLink>
        <NavLink to="/history" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Clock /> History
        </NavLink>
      </nav>

      <div className="sidebar-status">
        <div className="nav-section-title">Nodes ({onlineCount}/4 online)</div>
        {nodeStatuses.map((node) => (
          <div className="status-item" key={node.name}>
            <span className={`status-dot ${node.status === 'online' ? 'online' : 'offline'}`} />
            {node.name}
          </div>
        ))}
        {nodeStatuses.length === 0 &&
          ['coordinator1', 'member2', 'member3', 'member4'].map((name) => (
            <div className="status-item" key={name}>
              <span className="status-dot offline" />
              {name}
            </div>
          ))}
      </div>
    </aside>
  );
}
