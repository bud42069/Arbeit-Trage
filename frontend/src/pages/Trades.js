import React, { useState, useEffect, useCallback } from 'react';
import { Download, ExternalLink } from 'lucide-react';
import { useWebSocketSubscription } from '../hooks/useWebSocket';
import { toast } from 'sonner';

const Trades = () => {
  const [trades, setTrades] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    totalPnl: 0,
    avgLatency: 0
  });
  const [totalCountFromDB, setTotalCountFromDB] = useState(0);  // Preserve DB total

  // WebSocket real-time updates
  const { isConnected } = useWebSocketSubscription('trade', useCallback((newTrade) => {
    setTrades(prev => {
      const updated = [newTrade, ...prev].slice(0, 100);  // Keep only 100 visible
      
      // Recalculate stats for visible trades only
      const totalPnl = updated.reduce((sum, t) => sum + (parseFloat(t.pnl_abs) || 0), 0);
      const avgLatency = updated.reduce((sum, t) => sum + (parseInt(t.latency_ms) || 0), 0) / updated.length;
      
      // Increment total count (new trade added to DB)
      setStats(prev => ({
        total: prev.total + 1,  // Increment, don't replace!
        totalPnl,
        avgLatency
      }));
      
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
        
        // Calculate stats using actual total count from database
        if (data.trades && data.trades.length > 0) {
          const totalPnl = data.trades.reduce((sum, t) => sum + (parseFloat(t.pnl_abs) || 0), 0);
          const avgLatency = data.trades.reduce((sum, t) => sum + (parseInt(t.latency_ms) || 0), 0) / data.trades.length;
          
          const dbTotal = data.total_count || data.trades.length;
          setTotalCountFromDB(dbTotal);  // Store DB total
          
          setStats({
            total: dbTotal,  // Use total_count from API
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

  const handleExportCSV = async () => {
    if (trades.length === 0) return;
    
    try {
      // Show loading toast
      toast.info('Exporting all trades...', {
        description: 'Fetching complete trade history from database'
      });
      
      // First, get the total count
      const countResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/trades?limit=1`);
      const countData = await countResponse.json();
      const totalCount = countData.total_count || 0;
      
      if (totalCount === 0) {
        toast.error('No trades to export');
        return;
      }
      
      // Fetch ALL trades (use total_count + buffer for safety)
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/trades?limit=${totalCount + 100}`);
      const data = await response.json();
      const allTrades = data.trades || [];
      
      // Generate CSV from ALL trades
      const headers = ['Timestamp', 'Asset', 'Direction', 'Size USD', 'CEX Price', 'DEX Price', 'PnL USD', 'PnL %', 'Latency ms', 'Status'];
      const rows = allTrades.map(t => [
        new Date(t.timestamp).toISOString(),
        t.asset,
        t.direction,
        (parseFloat(t.size_asset) * parseFloat(t.cex_price)).toFixed(2),
        parseFloat(t.cex_price).toFixed(6),
        parseFloat(t.dex_price).toFixed(6),
        parseFloat(t.pnl_abs).toFixed(2),
        parseFloat(t.pnl_pct).toFixed(2),
        parseInt(t.latency_ms).toFixed(0),
        t.status
      ]);
      
      const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Timestamp in filename for uniqueness
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      a.download = `trades_complete_${timestamp}.csv`;
      a.click();
      
      // Success toast
      toast.success(`Exported ${allTrades.length} trades`, {
        description: `File: trades_complete_${timestamp}.csv`
      });
      
    } catch (error) {
      console.error('Export failed:', error);
      toast.error('Export failed', {
        description: 'Could not fetch complete trade history'
      });
    }
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
                      {new Date(trade.timestamp).toLocaleString('en-US', { 
                        timeZone: 'America/New_York',
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: true
                      })} ET
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-primary">
                      {trade.asset}
                    </td>
                    <td className="px-6 py-4 text-sm text-secondary">
                      {trade.direction === 'cex_to_dex' ? 'CEX → DEX' : 'DEX → CEX'}
                    </td>
                    <td className="px-6 py-4 text-right text-sm tabular text-secondary">
                      ${(parseFloat(trade.size_asset) * parseFloat(trade.cex_price)).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-right text-sm tabular text-tertiary mono">
                      ${parseFloat(trade.cex_price).toFixed(6)}
                    </td>
                    <td className="px-6 py-4 text-right text-sm tabular text-tertiary mono">
                      ${parseFloat(trade.dex_price).toFixed(6)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex flex-col items-end">
                        <span className={`text-sm font-medium tabular ${
                          parseFloat(trade.pnl_abs) >= 0 ? 'text-success' : 'text-danger'
                        }`}>
                          {parseFloat(trade.pnl_abs) >= 0 ? '+' : ''}${parseFloat(trade.pnl_abs).toFixed(2)}
                        </span>
                        <span className="text-xs text-tertiary tabular">
                          {parseFloat(trade.pnl_pct) >= 0 ? '+' : ''}{parseFloat(trade.pnl_pct).toFixed(2)}%
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
