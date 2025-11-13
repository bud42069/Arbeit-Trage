import React, { useState, useEffect } from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { DollarSign, TrendingUp, Clock, Activity } from 'lucide-react';

const Overview = () => {
  const [kpis, setKpis] = useState({
    netPnl: 0,
    captureRate: 0,
    p95Latency: 0,
    activeWindows: 0,
    pnlHistory: []
  });

  useEffect(() => {
    // Fetch KPIs from multiple endpoints
    const fetchKpis = async () => {
      try {
        // Fetch status for system info
        const statusResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/status`);
        const statusData = await statusResponse.json();
        
        // Fetch recent trades for PnL
        const tradesResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/trades?limit=100`);
        const tradesData = await tradesResponse.json();
        
        // Calculate metrics from trades
        const trades = tradesData.trades || [];
        const totalPnl = trades.reduce((sum, t) => sum + (parseFloat(t.pnl_abs) || 0), 0);
        const avgLatency = trades.length > 0 
          ? trades.reduce((sum, t) => sum + (parseInt(t.latency_ms) || 0), 0) / trades.length 
          : 0;
        
        // Calculate p95 latency
        const latencies = trades.map(t => parseInt(t.latency_ms) || 0).sort((a, b) => a - b);
        const p95Index = Math.floor(latencies.length * 0.95);
        const p95Latency = latencies[p95Index] || 0;
        
        // Generate PnL sparkline from recent trades
        const recentTrades = trades.slice(0, 20).reverse();
        let cumulativePnl = 0;
        const sparkline = recentTrades.map(t => {
          cumulativePnl += parseFloat(t.pnl_abs) || 0;
          return { value: cumulativePnl };
        });
        
        // Fetch opportunities for capture rate
        const oppsResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/opportunities?limit=100`);
        const oppsData = await oppsResponse.json();
        const opportunities = oppsData.opportunities || [];
        
        // Calculate capture rate (trades / opportunities)
        const captureRate = opportunities.length > 0 
          ? (trades.length / opportunities.length) * 100 
          : 0;
        
        setKpis({
          netPnl: totalPnl,
          captureRate: captureRate,
          p95Latency: p95Latency,
          activeWindows: trades.length,
          pnlHistory: sparkline.length > 0 ? sparkline : [{ value: 0 }]
        });
      } catch (error) {
        console.error('Failed to fetch KPIs:', error);
      }
    };

    fetchKpis();
    const interval = setInterval(fetchKpis, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6" data-testid="overview-screen">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-semibold">Overview</h1>
        <p className="text-secondary mt-1">Live system performance and key metrics</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Net PnL (24h)"
          value={kpis.netPnl}
          format="currency"
          icon={DollarSign}
          sparkline={kpis.pnlHistory}
          testId="kpi-net-pnl"
        />
        
        <KPICard
          title="Capture Rate"
          value={kpis.captureRate}
          format="percent"
          icon={TrendingUp}
          testId="kpi-capture-rate"
        />
        
        <KPICard
          title="p95 Latency"
          value={kpis.p95Latency}
          format="ms"
          icon={Clock}
          testId="kpi-latency"
        />
        
        <KPICard
          title="Active Windows"
          value={kpis.activeWindows}
          format="number"
          icon={Activity}
          testId="kpi-windows"
        />
      </div>

      {/* Additional sections will be added */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <div className="text-secondary text-center py-12">
          <p>Live trade stream and opportunity heatmap coming soon</p>
        </div>
      </div>
    </div>
  );
};

// KPI Card Component
const KPICard = ({ title, value, format, icon: Icon, sparkline, testId }) => {
  const formatValue = (val) => {
    if (format === 'currency') {
      const sign = val >= 0 ? '+' : '';
      return `${sign}$${Math.abs(val).toFixed(2)}`;
    }
    if (format === 'percent') {
      return `${val.toFixed(1)}%`;
    }
    if (format === 'ms') {
      return `${val.toFixed(0)}ms`;
    }
    return val.toString();
  };

  const getValueColor = () => {
    if (format === 'currency') {
      return value >= 0 ? 'text-success' : 'text-danger';
    }
    return 'text-primary';
  };

  return (
    <div className="card" data-testid={testId}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-sm text-secondary">{title}</p>
          <p className={`text-2xl font-semibold mt-1 tabular ${getValueColor()}`}>
            {formatValue(value)}
          </p>
        </div>
        <div className="p-2 rounded-lg bg-surface-2">
          <Icon size={20} className="text-lime-400" />
        </div>
      </div>
      
      {sparkline && sparkline.length > 0 && (
        <div className="h-12 -mx-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparkline}>
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="var(--accent)" 
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default Overview;
