import React, { useState, useEffect, useCallback } from 'react';
import { Search, Filter, TrendingUp, TrendingDown } from 'lucide-react';
import { useWebSocketSubscription } from '../hooks/useWebSocket';

const Opportunities = () => {
  const [opportunities, setOpportunities] = useState([]);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // WebSocket real-time updates
  const { isConnected } = useWebSocketSubscription('opportunity', useCallback((newOpp) => {
    setOpportunities(prev => [newOpp, ...prev].slice(0, 50)); // Keep last 50
  }, []));

  useEffect(() => {
    // Fetch initial opportunities from API
    const fetchOpportunities = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/opportunities`);
        const data = await response.json();
        setOpportunities(data.opportunities || []);
      } catch (error) {
        console.error('Failed to fetch opportunities:', error);
      }
    };

    fetchOpportunities();
  }, []);

  const filteredOpportunities = opportunities.filter(opp => {
    if (searchTerm && !opp.asset.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6" data-testid="opportunities-screen">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Opportunities</h1>
          <p className="text-secondary mt-1">Live arbitrage signals detected by the engine</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-tertiary" size={18} />
            <input
              type="text"
              placeholder="Search asset..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              data-testid="search-input"
              className="
                pl-10 pr-4 py-2 rounded-lg
                bg-surface-2 border border-strong
                text-sm text-primary
                focus:outline-none focus:ring-2 focus:ring-lime-400/50
                w-64
              "
            />
          </div>
        </div>
      </div>

      {/* Opportunities Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="opportunities-table">
            <thead>
              <tr className="border-b border-subtle">
                <th className="text-left px-6 py-4 text-sm font-medium text-secondary">Timestamp</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-secondary">Asset</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-secondary">Direction</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-secondary">Net PnL</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-secondary">Spread</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-secondary">Size</th>
              </tr>
            </thead>
            <tbody>
              {filteredOpportunities.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-12 text-secondary">
                    <p>No opportunities detected yet</p>
                    <p className="text-sm text-tertiary mt-1">Waiting for arbitrage signals...</p>
                  </td>
                </tr>
              ) : (
                filteredOpportunities.map((opp) => (
                  <tr 
                    key={opp.id} 
                    className="border-b border-subtle hover:bg-surface-2/50 transition-colors"
                    data-testid="opportunity-row"
                  >
                    <td className="px-6 py-4 text-sm text-tertiary mono">
                      {new Date(opp.timestamp).toLocaleString('en-US', { 
                        timeZone: 'America/New_York',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: true
                      })} ET
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-primary">
                      {opp.asset}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 text-sm ${
                        opp.direction === 'cex_to_dex' ? 'text-buy' : 'text-sell'
                      }`}>
                        {opp.direction === 'cex_to_dex' ? (
                          <><TrendingUp size={14} /> CEX → DEX</>
                        ) : (
                          <><TrendingDown size={14} /> DEX → CEX</>
                        )}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right text-sm font-medium tabular text-success">
                      +{Number(opp.predicted_pnl_pct).toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 text-right text-sm tabular text-secondary">
                      {Number(opp.spread_pct || 0).toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 text-right text-sm tabular text-secondary">
                      ${Number(opp.size_usd || opp.size).toFixed(2)}
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

export default Opportunities;
