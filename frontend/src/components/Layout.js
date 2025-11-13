import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  TrendingUp, 
  FileText, 
  Activity,
  Circle,
  Pause,
  Play
} from 'lucide-react';

export const Layout = ({ children }) => {
  const location = useLocation();
  const [status, setStatus] = useState({
    gemini: 'degraded',
    coinbase: 'degraded',
    solana: 'degraded',
    observeOnly: false,
    isPaused: false
  });

  // Fetch status from API
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/status`);
        const data = await response.json();
        
        // Parse connections object correctly
        const connections = data.connections || {};
        const risk = data.risk || {};
        
        setStatus({
          gemini: connections.gemini ? 'healthy' : 'down',
          coinbase: connections.coinbase ? 'healthy' : 'degraded',
          solana: connections.solana ? 'healthy' : 'down',
          observeOnly: risk.observe_only || false,
          isPaused: risk.is_paused || false
        });
      } catch (error) {
        console.error('Failed to fetch status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const navigation = [
    { name: 'Overview', path: '/overview', icon: LayoutDashboard },
    { name: 'Opportunities', path: '/opportunities', icon: TrendingUp },
    { name: 'Trades', path: '/trades', icon: FileText },
    { name: 'Execution', path: '/execution', icon: Activity },
    { name: 'Inventory', path: '/inventory', icon: Circle },
    { name: 'Risk & Limits', path: '/risk', icon: Circle },
  ];

  const getStatusColor = (status) => {
    if (status === 'healthy') return 'bg-lime-400';
    if (status === 'degraded') return 'bg-warning';
    return 'bg-danger';
  };

  const handlePauseResume = async () => {
    const endpoint = status.isPaused ? 'resume' : 'pause';
    try {
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/controls/${endpoint}`, {
        method: 'POST'
      });
    } catch (error) {
      console.error(`Failed to ${endpoint}:`, error);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] flex" data-testid="app-layout">
      {/* Sidebar */}
      <aside className="w-64 bg-surface-1 border-r border-strong flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-subtle">
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <Activity className="text-lime-400" size={24} />
            <span>ARB</span>
            <span className="text-secondary text-sm">Engine</span>
          </h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2" data-testid="sidebar-nav">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                data-testid={`nav-${item.name.toLowerCase()}`}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg
                  transition-all duration-150 group
                  ${
                    isActive
                      ? 'bg-lime-400/10 text-lime-400 border-l-2 border-lime-400'
                      : 'text-secondary hover:text-primary hover:bg-surface-2'
                  }
                `}
              >
                <Icon size={20} />
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Mode Indicators */}
        <div className="p-4 space-y-3 border-t border-subtle">
          {status.observeOnly && (
            <div 
              className="px-3 py-2 rounded-lg bg-warning/10 border border-warning/30 text-warning text-sm"
              data-testid="observe-only-indicator"
            >
              <span className="font-medium">OBSERVE ONLY</span>
            </div>
          )}
          
          {status.isPaused && (
            <div 
              className="px-3 py-2 rounded-lg bg-danger/10 border border-danger/30 text-danger text-sm"
              data-testid="paused-indicator"
            >
              <span className="font-medium">SYSTEM PAUSED</span>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <header className="h-16 bg-surface-1 border-b border-strong flex items-center justify-between px-6">
          {/* Status Pills */}
          <div className="flex items-center gap-4" data-testid="status-pills">
            <StatusPill 
              label="Gemini" 
              status={status.gemini} 
              data-testid="status-gemini"
            />
            <StatusPill 
              label="Coinbase" 
              status={status.coinbase}
              data-testid="status-coinbase"
            />
            <StatusPill 
              label="Solana" 
              status={status.solana}
              data-testid="status-solana"
            />
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={handlePauseResume}
              data-testid="pause-resume-button"
              className="
                flex items-center gap-2 px-4 py-2 rounded-lg
                bg-surface-2 border border-strong
                text-sm font-medium text-secondary
                hover:bg-surface-3 hover:text-primary
                transition-all duration-150
                focus-ring
              "
            >
              {status.isPaused ? (
                <><Play size={16} /> Resume</>
              ) : (
                <><Pause size={16} /> Pause</>
              )}
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

// Status Pill Component
const StatusPill = ({ label, status }) => {
  const statusColors = {
    healthy: 'bg-lime-400',
    degraded: 'bg-warning',
    down: 'bg-danger'
  };

  const statusText = {
    healthy: 'Connected',
    degraded: 'Degraded',
    down: 'Disconnected'
  };

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-2">
      <div className="relative">
        <Circle 
          size={8} 
          className={`${statusColors[status]} fill-current`}
        />
        {status === 'healthy' && (
          <Circle 
            size={8} 
            className="absolute inset-0 animate-pulse-lime fill-current text-lime-400/40"
          />
        )}
      </div>
      <span className="text-sm text-secondary">{label}</span>
      <span className="text-xs text-tertiary">•</span>
      <span className="text-xs text-tertiary">{statusText[status]}</span>
    </div>
  );
};

export default Layout;
