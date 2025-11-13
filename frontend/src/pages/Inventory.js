import React, { useState, useEffect } from 'react';
import { Wallet, TrendingUp, TrendingDown, RefreshCw, AlertCircle } from 'lucide-react';

const Inventory = () => {
  const [balances, setBalances] = useState({
    gemini: { sol: 0, usdc: 0, total_usd: 0 },
    solana: { sol: 0, usdc: 0, total_usd: 0 }
  });

  const [drift, setDrift] = useState({
    sol_drift: 0,
    usdc_drift: 0,
    rebalance_needed: false
  });

  useEffect(() => {
    // For POC, show mock inventory data
    // In production, this would fetch from /api/v1/inventory
    const mockData = {
      gemini: { sol: 50.0, usdc: 5000.0, total_usd: 12250.0 },
      solana: { sol: 48.5, usdc: 5200.0, total_usd: 12235.0 }
    };

    setBalances(mockData);
    
    // Calculate drift
    const totalSol = mockData.gemini.sol + mockData.solana.sol;
    const totalUsdc = mockData.gemini.usdc + mockData.solana.usdc;
    const solDriftPct = ((mockData.gemini.sol - mockData.solana.sol) / totalSol) * 100;
    const usdcDriftPct = ((mockData.gemini.usdc - mockData.solana.usdc) / totalUsdc) * 100;
    
    setDrift({
      sol_drift: solDriftPct,
      usdc_drift: usdcDriftPct,
      rebalance_needed: Math.abs(solDriftPct) > 10 || Math.abs(usdcDriftPct) > 10
    });
  }, []);

  const totalSol = balances.gemini.sol + balances.solana.sol;
  const totalUsdc = balances.gemini.usdc + balances.solana.usdc;
  const totalUsd = balances.gemini.total_usd + balances.solana.total_usd;

  return (
    <div className="space-y-6" data-testid="inventory-screen">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Inventory & Rebalance</h1>
          <p className="text-secondary mt-1">Cross-venue balance tracking and rebalancing tools</p>
        </div>

        <button
          data-testid="rebalance-button"
          disabled={!drift.rebalance_needed}
          className="
            flex items-center gap-2 px-4 py-2 rounded-lg
            bg-lime-400 text-[var(--accent-contrast)]
            text-sm font-medium
            hover:bg-lime-500
            disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-surface-3
            transition-all duration-150
            focus-ring
          "
        >
          <RefreshCw size={16} />
          Rebalance
        </button>
      </div>

      {/* Total Portfolio */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-secondary">Total Value</p>
          <p className="text-2xl font-semibold mt-1 text-primary tabular" data-testid="total-value">
            ${totalUsd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-secondary">Total SOL</p>
          <p className="text-2xl font-semibold mt-1 text-primary tabular">
            {totalSol.toFixed(2)}
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-secondary">Total USDC</p>
          <p className="text-2xl font-semibold mt-1 text-primary tabular">
            ${totalUsdc.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      {/* Drift Alert */}
      {drift.rebalance_needed && (
        <div 
          className="flex items-start gap-3 p-4 rounded-lg bg-warning/10 border border-warning/30"
          data-testid="rebalance-alert"
        >
          <AlertCircle size={20} className="text-warning mt-0.5" />
          <div>
            <p className="text-sm font-medium text-warning">Rebalance Recommended</p>
            <p className="text-xs text-secondary mt-1">
              Asset distribution drift exceeds 10% threshold. Consider rebalancing to maintain optimal inventory levels.
            </p>
          </div>
        </div>
      )}

      {/* Venue Balances */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gemini */}
        <VenueCard
          venue="Gemini (CEX)"
          icon="💎"
          balances={balances.gemini}
          drift={{ sol: drift.sol_drift, usdc: drift.usdc_drift }}
        />

        {/* Solana */}
        <VenueCard
          venue="Solana (DEX)"
          icon="◎"
          balances={balances.solana}
          drift={{ sol: -drift.sol_drift, usdc: -drift.usdc_drift }}
        />
      </div>

      {/* Rebalancing Plan (Placeholder) */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Suggested Rebalancing Actions</h3>
        
        {drift.rebalance_needed ? (
          <div className="space-y-3">
            {Math.abs(drift.sol_drift) > 10 && (
              <RebalanceAction
                asset="SOL"
                fromVenue={drift.sol_drift > 0 ? "Gemini" : "Solana"}
                toVenue={drift.sol_drift > 0 ? "Solana" : "Gemini"}
                amount={Math.abs((drift.sol_drift / 100) * totalSol).toFixed(2)}
                reason={`${Math.abs(drift.sol_drift).toFixed(1)}% distribution imbalance`}
              />
            )}
            {Math.abs(drift.usdc_drift) > 10 && (
              <RebalanceAction
                asset="USDC"
                fromVenue={drift.usdc_drift > 0 ? "Gemini" : "Solana"}
                toVenue={drift.usdc_drift > 0 ? "Solana" : "Gemini"}
                amount={Math.abs((drift.usdc_drift / 100) * totalUsdc).toFixed(2)}
                reason={`${Math.abs(drift.usdc_drift).toFixed(1)}% distribution imbalance`}
              />
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-secondary">
            <p className="text-sm">No rebalancing needed</p>
            <p className="text-xs text-tertiary mt-1">Asset distribution is within acceptable thresholds</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Venue Card Component
const VenueCard = ({ venue, icon, balances, drift }) => (
  <div className="card" data-testid={`venue-${venue.toLowerCase()}`}>
    <div className="flex items-center gap-2 mb-4">
      <span className="text-2xl">{icon}</span>
      <h3 className="text-lg font-semibold">{venue}</h3>
    </div>

    <div className="space-y-4">
      {/* SOL Balance */}
      <BalanceRow
        asset="SOL"
        amount={balances.sol}
        drift={drift.sol}
      />

      {/* USDC Balance */}
      <BalanceRow
        asset="USDC"
        amount={balances.usdc}
        drift={drift.usdc}
      />

      {/* Total Value */}
      <div className="pt-4 border-t border-subtle">
        <div className="flex items-center justify-between">
          <span className="text-sm text-secondary">Total Value</span>
          <span className="text-lg font-semibold text-primary tabular">
            ${balances.total_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
      </div>
    </div>
  </div>
);

// Balance Row Component
const BalanceRow = ({ asset, amount, drift }) => {
  const isDrifted = Math.abs(drift) > 10;
  
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Wallet size={16} className="text-tertiary" />
        <span className="text-sm text-secondary">{asset}</span>
      </div>
      
      <div className="flex items-center gap-3">
        <span className="text-base font-semibold text-primary tabular">
          {asset === 'USDC' ? `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : amount.toFixed(2)}
        </span>
        
        {isDrifted && (
          <div className={`flex items-center gap-1 text-xs ${drift > 0 ? 'text-success' : 'text-danger'}`}>
            {drift > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            <span>{Math.abs(drift).toFixed(1)}%</span>
          </div>
        )}
      </div>
    </div>
  );
};

// Rebalance Action Component
const RebalanceAction = ({ asset, fromVenue, toVenue, amount, reason }) => (
  <div className="flex items-start gap-3 p-4 bg-surface-2 rounded-lg border border-subtle">
    <div className="w-8 h-8 rounded-full bg-lime-400/10 flex items-center justify-center flex-shrink-0">
      <RefreshCw size={16} className="text-lime-400" />
    </div>
    
    <div className="flex-1">
      <p className="text-sm font-medium text-primary">
        Transfer {amount} {asset} from {fromVenue} → {toVenue}
      </p>
      <p className="text-xs text-secondary mt-1">{reason}</p>
    </div>
    
    <button
      className="
        px-3 py-1.5 rounded-md bg-surface-3 border border-subtle
        text-xs font-medium text-secondary
        hover:bg-surface-1 hover:text-primary
        transition-all duration-150
      "
    >
      Execute
    </button>
  </div>
);

// Detail Item Component
const DetailItem = ({ label, value, sublabel, valueColor = 'text-primary' }) => (
  <div>
    <p className="text-xs text-secondary mb-1">{label}</p>
    <p className={`text-base font-semibold tabular ${valueColor}`}>{value}</p>
    {sublabel && <p className="text-xs text-tertiary mt-0.5">{sublabel}</p>}
  </div>
);

export default Inventory;
