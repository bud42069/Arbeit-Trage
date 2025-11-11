import React, { useState, useEffect, useCallback } from 'react';
import { Download, ExternalLink } from 'lucide-react';
import { useWebSocketSubscription } from '../hooks/useWebSocket';

const Trades = () => {
  const [trades, setTrades] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    totalPnl: 0,
    avgLatency: 0
  });

  // WebSocket real-time updates
  const { isConnected } = useWebSocketSubscription('trade', useCallback((newTrade) => {
    setTrades(prev => {
      const updated = [newTrade, ...prev];
      
      // Recalculate stats
      const totalPnl = updated.reduce((sum, t) => sum + t.pnl_usd, 0);
      const avgLatency = updated.reduce((sum, t) => sum + t.latency_ms, 0) / updated.length;
      
      setStats({
        total: updated.length,
        totalPnl,
        avgLatency
      });
      
      return updated;
    });
  }, []));

  useEffect(() => {
    // Fetch initial trades from API
    const fetchTrades = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/trades`);
        const data = await response.json();
        setTrades(data.trades || []);
        
        // Calculate stats
        if (data.trades && data.trades.length > 0) {
          const totalPnl = data.trades.reduce((sum, t) => sum + t.pnl_usd, 0);
          const avgLatency = data.trades.reduce((sum, t) => sum + t.latency_ms, 0) / data.trades.length;
          
          setStats({
            total: data.trades.length,
            totalPnl,
            avgLatency
          });
        }
      } catch (error) {
        console.error('Failed to fetch trades:', error);
      }
    };

    fetchTrades();
  }, []);

  const handleExportCSV = () => {
    if (trades.length === 0) return;
    
    // Generate CSV
    const headers = ['Timestamp', 'Asset', 'Direction', 'Size USD', 'CEX Price', 'DEX Price', 'PnL USD', 'PnL %', 'Latency ms'];
    const rows = trades.map(t => [
      new Date(t.timestamp).toISOString(),
      t.asset,
      t.direction,
      t.size_usd.toFixed(2),
      t.cex_price.toFixed(6),
      t.dex_price.toFixed(6),
      t.pnl_usd.toFixed(2),
      t.pnl_pct.toFixed(2),
      t.latency_ms.toFixed(0)
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trades_${Date.now()}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6" data-testid="trades-screen">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Trades</h1>
          <p className="text-secondary mt-1">Complete ledger of executed arbitrage trades</p>
        </div>
        
        <button
          onClick={handleExportCSV}
          disabled={trades.length === 0}
          data-testid="export-csv-button"
          className="
            flex items-center gap-2 px-4 py-2 rounded-lg
            bg-lime-400 text-[var(--accent-contrast)]
            text-sm font-medium
            hover:bg-lime-500
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-all duration-150
            focus-ring
          "
        >
          <Download size={16} />
          Export CSV
        </button>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-secondary">Total Trades</p>
          <p className="text-2xl font-semibold mt-1 text-primary tabular" data-testid="stat-total-trades">
            {stats.total}
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-secondary">Total PnL</p>
          <p className={`text-2xl font-semibold mt-1 tabular ${
            stats.totalPnl >= 0 ? 'text-success' : 'text-danger'
          }`} data-testid="stat-total-pnl">
            {stats.totalPnl >= 0 ? '+' : ''}${stats.totalPnl.toFixed(2)}
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-secondary">Avg Latency</p>
          <p className="text-2xl font-semibold mt-1 text-primary tabular" data-testid="stat-avg-latency">
            {stats.avgLatency.toFixed(0)}ms
          </p>
        </div>
      </div>

      {/* Trades Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="trades-table">
            <thead>
              <tr className="border-b border-subtle">
                <th className="text-left px-6 py-4 text-sm font-medium text-secondary">Timestamp</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-secondary">Asset</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-secondary">Direction</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-secondary">Size</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-secondary">CEX Price</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-secondary">DEX Price</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-secondary">PnL</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-secondary">Latency</th>
              </tr>
            </thead>
            <tbody>
              {trades.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-12 text-secondary">
                    <p>No trades executed yet</p>
                    <p className="text-sm text-tertiary mt-1">Trades will appear here once execution begins</p>
                  </td>
                </tr>
              ) : (
                trades.map((trade) => (
                  <tr 
                    key={trade.id} 
                    className="border-b border-subtle hover:bg-surface-2/50 transition-colors"
                    data-testid="trade-row"
                  >
                    <td className="px-6 py-4 text-sm text-tertiary mono">
                      {new Date(trade.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-primary">
                      {trade.asset}
                    </td>
                    <td className="px-6 py-4 text-sm text-secondary">
                      {trade.direction === 'cex_to_dex' ? 'CEX → DEX' : 'DEX → CEX'}
                    </td>
                    <td className="px-6 py-4 text-right text-sm tabular text-secondary">
                      ${trade.size_usd.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-right text-sm tabular text-tertiary mono">
                      ${trade.cex_price.toFixed(6)}
                    </td>
                    <td className="px-6 py-4 text-right text-sm tabular text-tertiary mono">
                      ${trade.dex_price.toFixed(6)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex flex-col items-end">
                        <span className={`text-sm font-medium tabular ${
                          trade.pnl_usd >= 0 ? 'text-success' : 'text-danger'
                        }`}>
                          {trade.pnl_usd >= 0 ? '+' : ''}${trade.pnl_usd.toFixed(2)}
                        </span>
                        <span className="text-xs text-tertiary tabular">
                          {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right text-sm tabular text-tertiary">
                      {trade.latency_ms.toFixed(0)}ms
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Trades;
