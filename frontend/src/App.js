import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import Opportunities from './pages/Opportunities';
import Trades from './pages/Trades';
import ExecutionMonitor from './pages/ExecutionMonitor';
import Inventory from './pages/Inventory';
import RiskLimits from './pages/RiskLimits';
import './index.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<Overview />} />
          <Route path="/opportunities" element={<Opportunities />} />
          <Route path="/trades" element={<Trades />} />
          <Route path="/execution" element={<ExecutionMonitor />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/risk" element={<RiskLimits />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
