import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, TrendingUp, TrendingDown, Activity } from 'lucide-react';

const ExecutionMonitor = () => {
  const [trades, setTrades] = useState([]);
  const [selectedTrade, setSelectedTrade] = useState(null);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/trades?limit=20`);
        const data = await response.json();
        setTrades(data.trades || []);
        
        // Auto-select most recent trade
        if (data.trades && data.trades.length > 0 && !selectedTrade) {
          setSelectedTrade(data.trades[0]);
        }
      } catch (error) {
        console.error('Failed to fetch trades:', error);
      }
    };

    fetchTrades();
    const interval = setInterval(fetchTrades, 3000);
    return () => clearInterval(interval);
  }, [selectedTrade]);

  return (
    <div className="space-y-6" data-testid="execution-monitor-screen">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-semibold">Execution Monitor</h1>
        <p className="text-secondary mt-1">Dual-leg trade execution timeline and analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trade List */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-lg font-semibold text-primary">Recent Executions</h2>
          
          <div className="space-y-2 max-h-[700px] overflow-y-auto pr-2" data-testid="trade-list">
            {trades.length === 0 ? (
              <div className="card p-6 text-center text-secondary">
                <Activity size={32} className="mx-auto mb-2 text-tertiary" />
                <p className="text-sm">No executions yet</p>
                <p className="text-xs text-tertiary mt-1">Simulated trades will appear here</p>
              </div>
            ) : (
              trades.map((trade) => (
                <TradeCard
                  key={trade.trade_id}
                  trade={trade}
                  isSelected={selectedTrade?.trade_id === trade.trade_id}
                  onClick={() => setSelectedTrade(trade)}
                />
              ))
            )}
          </div>
        </div>

        {/* Trade Details */}
        <div className="lg:col-span-2 space-y-4">
          {selectedTrade ? (
            <>
              <TradeTimeline trade={selectedTrade} />
              <TradeDetails trade={selectedTrade} />
            </>
          ) : (
            <div className="card h-[500px] flex items-center justify-center">
              <div className="text-center text-secondary">
                <Activity size={48} className="mx-auto mb-4 text-tertiary" />
                <p>Select a trade to view execution details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Trade Card Component
const TradeCard = ({ trade, isSelected, onClick }) => {
  const pnlAbs = parseFloat(trade.pnl_abs);
  const pnlPct = parseFloat(trade.pnl_pct);
  const isProfitable = pnlAbs >= 0;

  return (
    <div
      onClick={onClick}
      data-testid="execution-trade-card"
      className={`
        card cursor-pointer transition-all duration-150
        ${isSelected ? 'ring-2 ring-lime-400 bg-surface-2' : 'hover:bg-surface-2'}
      `}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {trade.direction === 'cex_to_dex' ? (
            <TrendingUp size={16} className="text-buy" />
          ) : (
            <TrendingDown size={16} className="text-sell" />
          )}
          <span className="text-sm font-medium text-primary">{trade.asset}</span>
        </div>
        
        <StatusBadge status={trade.status} />
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-tertiary">
          <Clock size={12} />
          <span className="mono">
            {new Date(trade.timestamp).toLocaleString('en-US', { 
              timeZone: 'America/New_York',
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: true
            })} ET
          </span>
        </div>

        <span className={`text-sm font-medium tabular ${
          isProfitable ? 'text-success' : 'text-danger'
        }`}>
          {isProfitable ? '+' : ''}${pnlAbs.toFixed(2)}
        </span>
      </div>
    </div>
  );
};

// Status Badge Component
const StatusBadge = ({ status }) => {
  const statusConfig = {
    filled: { icon: CheckCircle, color: 'text-success', label: 'Filled' },
    pending: { icon: Clock, color: 'text-warning', label: 'Pending' },
    failed: { icon: XCircle, color: 'text-danger', label: 'Failed' }
  };

  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-1 ${config.color}`}>
      <Icon size={14} />
      <span className="text-xs font-medium">{config.label}</span>
    </div>
  );
};

// Trade Timeline Component
const TradeTimeline = ({ trade }) => {
  const direction = trade.direction;
  const isCexFirst = direction === 'cex_to_dex';
  
  // Simulate timing breakdown (in production, this would come from actual execution logs)
  const totalLatencyMs = trade.latency_ms || 0;
  const leg1Latency = Math.floor(totalLatencyMs * 0.45);
  const leg2Latency = Math.floor(totalLatencyMs * 0.45);
  const overheadLatency = totalLatencyMs - leg1Latency - leg2Latency;

  return (
    <div className="card" data-testid="trade-timeline">
      <h3 className="text-lg font-semibold mb-4">Execution Timeline</h3>
      
      <div className="space-y-6">
        {/* Timeline Visualization */}
        <div className="relative">
          {/* Start */}
          <TimelineStep
            label="Opportunity Detected"
            time="T+0ms"
            status="completed"
            description={`Spread: ${trade.spread_pct || 'N/A'}%`}
          />

          {/* Leg 1 */}
          <TimelineStep
            label={isCexFirst ? "CEX Order Placed (Buy)" : "DEX Swap Initiated (Buy)"}
            time={`T+${leg1Latency}ms`}
            status="completed"
            description={isCexFirst ? `Order ID: ${trade.cex_order_id}` : `TX: ${trade.dex_tx_sig?.slice(0, 16)}...`}
            isLeg1
          />

          {/* Leg 2 */}
          <TimelineStep
            label={isCexFirst ? "DEX Swap Executed (Sell)" : "CEX Order Filled (Sell)"}
            time={`T+${leg1Latency + leg2Latency}ms`}
            status="completed"
            description={isCexFirst ? `TX: ${trade.dex_tx_sig?.slice(0, 16)}...` : `Order ID: ${trade.cex_order_id}`}
            isLeg2
          />

          {/* Complete */}
          <TimelineStep
            label="Both Legs Filled"
            time={`T+${totalLatencyMs}ms`}
            status="completed"
            description={`PnL: ${parseFloat(trade.pnl_abs) >= 0 ? '+' : ''}$${parseFloat(trade.pnl_abs).toFixed(2)}`}
            isLast
          />
        </div>

        {/* Latency Breakdown */}
        <div className="pt-4 border-t border-subtle">
          <h4 className="text-sm font-medium text-secondary mb-3">Latency Breakdown</h4>
          <div className="grid grid-cols-3 gap-4">
            <MetricCard
              label="Leg 1"
              value={`${leg1Latency}ms`}
              color="text-info"
            />
            <MetricCard
              label="Leg 2"
              value={`${leg2Latency}ms`}
              color="text-info"
            />
            <MetricCard
              label="Overhead"
              value={`${overheadLatency}ms`}
              color="text-tertiary"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Timeline Step Component
const TimelineStep = ({ label, time, status, description, isLeg1, isLeg2, isLast }) => {
  const statusColors = {
    completed: 'bg-success',
    pending: 'bg-warning',
    failed: 'bg-danger'
  };

  return (
    <div className="relative flex items-start gap-4 pb-6">
      {/* Connector Line */}
      {!isLast && (
        <div className="absolute left-[11px] top-6 bottom-0 w-0.5 bg-subtle" />
      )}

      {/* Status Dot */}
      <div className={`
        relative z-10 w-6 h-6 rounded-full ${statusColors[status]} 
        flex items-center justify-center
        ${status === 'completed' && (isLeg1 || isLeg2) ? 'ring-4 ring-lime-400/20' : ''}
      `}>
        {status === 'completed' && (
          <CheckCircle size={14} className="text-white" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 pt-0.5">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-primary">{label}</span>
          <span className="text-xs text-tertiary mono">{time}</span>
        </div>
        {description && (
          <p className="text-xs text-secondary mono">{description}</p>
        )}
      </div>
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ label, value, color = 'text-primary' }) => (
  <div className="bg-surface-2 rounded-lg p-3">
    <p className="text-xs text-secondary mb-1">{label}</p>
    <p className={`text-lg font-semibold tabular ${color}`}>{value}</p>
  </div>
);

// Trade Details Component
const TradeDetails = ({ trade }) => {
  const pnlAbs = parseFloat(trade.pnl_abs);
  const pnlPct = parseFloat(trade.pnl_pct);
  const sizeAsset = parseFloat(trade.size_asset);
  const cexPrice = parseFloat(trade.cex_price);
  const dexPrice = parseFloat(trade.dex_price);
  const fees = parseFloat(trade.fees_total);
  const sizeUsd = sizeAsset * cexPrice;

  return (
    <div className="card" data-testid="trade-details">
      <h3 className="text-lg font-semibold mb-4">Trade Details</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Size */}
        <DetailItem
          label="Size"
          value={`${sizeAsset.toFixed(2)} ${trade.asset.split('-')[0]}`}
          sublabel={`$${sizeUsd.toFixed(2)} USD`}
        />

        {/* CEX Price */}
        <DetailItem
          label="CEX Price"
          value={`$${cexPrice.toFixed(6)}`}
          sublabel={trade.direction === 'cex_to_dex' ? 'Entry (Buy)' : 'Exit (Sell)'}
        />

        {/* DEX Price */}
        <DetailItem
          label="DEX Price"
          value={`$${dexPrice.toFixed(6)}`}
          sublabel={trade.direction === 'cex_to_dex' ? 'Exit (Sell)' : 'Entry (Buy)'}
        />

        {/* Spread */}
        <DetailItem
          label="Price Spread"
          value={`${Math.abs(((dexPrice - cexPrice) / cexPrice) * 100).toFixed(3)}%`}
          sublabel={dexPrice > cexPrice ? 'DEX Premium' : 'CEX Premium'}
        />

        {/* Fees */}
        <DetailItem
          label="Total Fees"
          value={`$${fees.toFixed(2)}`}
          sublabel={`${((fees / sizeUsd) * 100).toFixed(2)}% of notional`}
        />

        {/* PnL USD */}
        <DetailItem
          label="Net PnL (USD)"
          value={`${pnlAbs >= 0 ? '+' : ''}$${pnlAbs.toFixed(2)}`}
          valueColor={pnlAbs >= 0 ? 'text-success' : 'text-danger'}
          sublabel="After all fees"
        />

        {/* PnL % */}
        <DetailItem
          label="Net PnL (%)"
          value={`${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`}
          valueColor={pnlPct >= 0 ? 'text-success' : 'text-danger'}
          sublabel="Return on capital"
        />

        {/* Latency */}
        <DetailItem
          label="Total Latency"
          value={`${trade.latency_ms}ms`}
          sublabel="Both legs filled"
        />
      </div>

      {/* Order IDs */}
      <div className="mt-6 pt-6 border-t border-subtle space-y-3">
        <h4 className="text-sm font-medium text-secondary mb-3">Order References</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="bg-surface-2 rounded-lg p-3">
            <p className="text-xs text-secondary mb-1">CEX Order ID</p>
            <p className="text-sm mono text-primary break-all">{trade.cex_order_id || 'N/A'}</p>
          </div>
          
          <div className="bg-surface-2 rounded-lg p-3">
            <p className="text-xs text-secondary mb-1">DEX Transaction</p>
            <p className="text-sm mono text-primary break-all">{trade.dex_tx_sig || 'N/A'}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Detail Item Component
const DetailItem = ({ label, value, sublabel, valueColor = 'text-primary' }) => (
  <div className="bg-surface-2 rounded-lg p-3">
    <p className="text-xs text-secondary mb-1">{label}</p>
    <p className={`text-base font-semibold tabular ${valueColor} mb-0.5`}>{value}</p>
    {sublabel && <p className="text-xs text-tertiary">{sublabel}</p>}
  </div>
);

export default ExecutionMonitor;
