import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, Activity, DollarSign, Clock, Zap } from 'lucide-react';
import { toast } from 'sonner';

const RiskLimits = () => {
  const [riskStatus, setRiskStatus] = useState({
    is_paused: false,
    pause_reason: null,
    daily_pnl_usd: 0,
    daily_trades: 0,
    daily_loss_limit_usd: 500,
    daily_remaining_loss_usd: 500,
    observe_only: true
  });

  const [settings, setSettings] = useState({
    max_position_size_usd: 1000,
    daily_loss_limit_usd: 500,
    max_slippage_bps: 75,
    staleness_threshold_sec: 10
  });

  useEffect(() => {
    const fetchRiskStatus = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/status`);
        const data = await response.json();
        
        if (data.risk) {
          setRiskStatus({
            is_paused: data.risk.is_paused || false,
            pause_reason: data.risk.pause_reason || null,
            daily_pnl_usd: data.risk.daily_pnl_usd || 0,
            daily_trades: data.risk.daily_trades || 0,
            daily_loss_limit_usd: data.risk.daily_loss_limit_usd || 500,
            daily_remaining_loss_usd: data.risk.daily_remaining_loss_usd || 500,
            observe_only: data.risk.observe_only || false
          });
        }
      } catch (error) {
        console.error('Failed to fetch risk status:', error);
      }
    };

    fetchRiskStatus();
    const interval = setInterval(fetchRiskStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handlePause = async () => {
    try {
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/controls/pause`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Failed to pause:', error);
    }
  };

  const handleResume = async () => {
    try {
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/controls/resume`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Failed to resume:', error);
    }
  };

  const handleModeToggle = async () => {
    try {
      const newMode = !riskStatus.observe_only;
      const endpoint = newMode ? '/api/v1/controls/observe-only' : '/api/v1/controls/live-trading';
      
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (res.ok) {
        setRiskStatus(prev => ({ ...prev, observe_only: newMode }));
        toast.success(newMode ? 'Switched to OBSERVE ONLY mode' : '⚠️ LIVE TRADING ENABLED', {
          description: newMode ? 'All trades will be simulated' : 'Real orders will be placed!',
        });
      } else {
        toast.error('Failed to change mode');
      }
    } catch (error) {
      toast.error('Error changing mode');
    }
  };

  const utilizationPct = ((settings.daily_loss_limit_usd - riskStatus.daily_remaining_loss_usd) / settings.daily_loss_limit_usd) * 100;

  return (
    <div className="space-y-6" data-testid="risk-limits-screen">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-semibold">Risk & Limits</h1>
        <p className="text-secondary mt-1">System controls, kill switches, and risk management</p>
      </div>

      {/* System Status Alert */}
      {riskStatus.is_paused && (
        <div 
          className="flex items-start gap-3 p-4 rounded-lg bg-danger/10 border border-danger/30"
          data-testid="system-paused-alert"
        >
          <AlertTriangle size={20} className="text-danger mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-danger">System Paused</p>
            <p className="text-xs text-secondary mt-1">{riskStatus.pause_reason || 'Manual pause activated'}</p>
          </div>
          <button
            onClick={handleResume}
            className="
              px-3 py-1.5 rounded-md bg-success/20 border border-success/30
              text-xs font-medium text-success
              hover:bg-success/30
              transition-all duration-150
            "
          >
            Resume
          </button>
        </div>
      )}

      {riskStatus.observe_only && !riskStatus.is_paused && (
        <div 
          className="flex items-start gap-3 p-4 rounded-lg bg-warning/10 border border-warning/30"
          data-testid="observe-only-alert"
        >
          <AlertTriangle size={20} className="text-warning mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-warning">OBSERVE ONLY Mode</p>
            <p className="text-xs text-secondary mt-1">System will detect opportunities but NOT execute real trades</p>
          </div>
          <button
            onClick={handleModeToggle}
            className="
              px-3 py-1.5 rounded-md bg-success/20 border border-success/30
              text-xs font-medium text-success
              hover:bg-success/30
              transition-all duration-150
            "
          >
            Enable Live Trading
          </button>
        </div>
      )}

      {!riskStatus.observe_only && !riskStatus.is_paused && (
        <div 
          className="flex items-start gap-3 p-4 rounded-lg bg-success/10 border border-success/30"
          data-testid="live-trading-alert"
        >
          <Zap size={20} className="text-success mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-success">LIVE TRADING Active</p>
            <p className="text-xs text-secondary mt-1">System is executing real trades with real funds</p>
          </div>
          <button
            onClick={handleModeToggle}
            className="
              px-3 py-1.5 rounded-md bg-warning/20 border border-warning/30
              text-xs font-medium text-warning
              hover:bg-warning/30
              transition-all duration-150
            "
          >
            Switch to Observe Only
          </button>
        </div>
      )}

      {/* Daily Limits */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <DollarSign size={20} className="text-lime-400" />
          Daily Loss Limits
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatCard
            label="Daily PnL"
            value={`${riskStatus.daily_pnl_usd >= 0 ? '+' : ''}$${riskStatus.daily_pnl_usd.toFixed(2)}`}
            valueColor={riskStatus.daily_pnl_usd >= 0 ? 'text-success' : 'text-danger'}
            icon={Activity}
          />
          
          <StatCard
            label="Trades Today"
            value={riskStatus.daily_trades}
            icon={Zap}
          />
          
          <StatCard
            label="Remaining Capacity"
            value={`$${Math.max(0, riskStatus.daily_remaining_loss_usd).toFixed(2)}`}
            valueColor={riskStatus.daily_remaining_loss_usd > 100 ? 'text-success' : 'text-warning'}
            icon={Shield}
          />
        </div>

        {/* Progress Bar */}
        <div>
          <div className="flex items-center justify-between text-xs text-secondary mb-2">
            <span>Loss Limit Utilization</span>
            <span className="font-medium">{Math.min(100, utilizationPct).toFixed(1)}%</span>
          </div>
          
          <div className="h-2 bg-surface-3 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                utilizationPct > 90 ? 'bg-danger' : utilizationPct > 70 ? 'bg-warning' : 'bg-success'
              }`}
              style={{ width: `${Math.min(100, utilizationPct)}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-xs text-tertiary mt-2">
            <span>$0</span>
            <span>${settings.daily_loss_limit_usd.toFixed(2)} limit</span>
          </div>
        </div>
      </div>

      {/* Risk Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Position Limits */}
        <div className="card">
          <h3 className="text-base font-semibold mb-4">Position Limits</h3>
          
          <div className="space-y-4">
            <LimitControl
              label="Max Position Size"
              value={settings.max_position_size_usd}
              unit="USD"
              icon={DollarSign}
            />
            
            <LimitControl
              label="Max Slippage"
              value={settings.max_slippage_bps / 100}
              unit="%"
              icon={Activity}
            />
            
            <LimitControl
              label="Staleness Threshold"
              value={settings.staleness_threshold_sec}
              unit="seconds"
              icon={Clock}
            />
          </div>
        </div>

        {/* Kill Switches */}
        <div className="card">
          <h3 className="text-base font-semibold mb-4">Kill Switches</h3>
          
          <div className="space-y-3">
            <KillSwitch
              label="Daily Loss Limit"
              isActive={riskStatus.daily_remaining_loss_usd <= 0}
              threshold={`$${settings.daily_loss_limit_usd} USD`}
              status={riskStatus.daily_remaining_loss_usd <= 0 ? 'triggered' : 'armed'}
            />
            
            <KillSwitch
              label="Data Staleness"
              isActive={false}
              threshold={`${settings.staleness_threshold_sec}s without update`}
              status="armed"
            />
            
            <KillSwitch
              label="Manual Override"
              isActive={riskStatus.is_paused}
              threshold="Operator control"
              status={riskStatus.is_paused ? 'triggered' : 'armed'}
            />
          </div>
        </div>
      </div>

      {/* Emergency Controls */}
      <div className="card bg-surface-2 border-danger/20">
        <h3 className="text-base font-semibold mb-4 text-danger flex items-center gap-2">
          <Shield size={20} />
          Emergency Controls
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            onClick={handlePause}
            disabled={riskStatus.is_paused}
            data-testid="emergency-pause-button"
            className="
              px-4 py-3 rounded-lg
              bg-danger/20 border border-danger/30
              text-sm font-medium text-danger
              hover:bg-danger/30
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-all duration-150
              focus-ring
            "
          >
            Emergency Pause
          </button>

          <button
            onClick={handleResume}
            disabled={!riskStatus.is_paused}
            data-testid="resume-button"
            className="
              px-4 py-3 rounded-lg
              bg-success/20 border border-success/30
              text-sm font-medium text-success
              hover:bg-success/30
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-all duration-150
              focus-ring
            "
          >
            Resume Trading
          </button>
        </div>
      </div>
    </div>
  );
};

// Stat Card Component
const StatCard = ({ label, value, valueColor = 'text-primary', icon: Icon }) => (
  <div className="bg-surface-2 rounded-lg p-4">
    <div className="flex items-center gap-2 mb-2">
      <Icon size={16} className="text-tertiary" />
      <p className="text-xs text-secondary">{label}</p>
    </div>
    <p className={`text-xl font-semibold tabular ${valueColor}`}>{value}</p>
  </div>
);

// Limit Control Component
const LimitControl = ({ label, value, unit, icon: Icon }) => (
  <div className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">
    <div className="flex items-center gap-2">
      <Icon size={16} className="text-tertiary" />
      <span className="text-sm text-secondary">{label}</span>
    </div>
    <span className="text-sm font-medium text-primary tabular">
      {value} {unit}
    </span>
  </div>
);

// Kill Switch Component
const KillSwitch = ({ label, isActive, threshold, status }) => (
  <div className={`
    flex items-start justify-between p-3 rounded-lg border
    ${isActive 
      ? 'bg-danger/10 border-danger/30' 
      : 'bg-surface-2 border-subtle'
    }
  `}>
    <div className="flex-1">
      <div className="flex items-center gap-2 mb-1">
        <Shield size={14} className={isActive ? 'text-danger' : 'text-tertiary'} />
        <span className="text-sm font-medium text-primary">{label}</span>
      </div>
      <p className="text-xs text-secondary">{threshold}</p>
    </div>
    
    <span className={`
      text-xs font-medium px-2 py-1 rounded-md
      ${isActive 
        ? 'bg-danger/20 text-danger' 
        : 'bg-success/20 text-success'
      }
    `}>
      {status}
    </span>
  </div>
);

export default RiskLimits;
