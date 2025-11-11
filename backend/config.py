"""Configuration management for arbitrage system."""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Solana / Helius
    solana_cluster: str = Field(default="mainnet-beta")
    helius_api_key: str
    helius_rpc_url: str
    helius_ws_url: str
    wsol_mint: str = "So11111111111111111111111111111111111111112"
    usdc_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    # Gemini
    gemini_enabled: bool = True
    gemini_base_url: str = "https://api.gemini.com"
    gemini_ws_public_url: str = "wss://api.gemini.com/v2/marketdata"
    gemini_ws_private_url: str = "wss://api.gemini.com/v1/order/events"
    gemini_api_key: str
    gemini_api_secret: str
    
    # Coinbase Advanced
    coinbase_adv_enabled: bool = False
    
    # Assets
    primary_symbol: str = "SOL-USD"
    asset_list: str = "SOL-USD,BTC-USD,ETH-USD"
    
    # MongoDB
    mongo_url: str = "mongodb://localhost:27017/arbitrage"
    
    # Observability
    prometheus_port: int = 9090
    log_level: str = "INFO"
    
    # Risk Controls
    observe_only_mode: bool = False
    max_position_size_usd: float = 1000.0
    daily_loss_limit_usd: float = 500.0
    
    # Feature Flags
    use_aggregator_fallback: bool = True
    auto_rebalance: bool = False
    priority_fee_auto: bool = True
    
    @property
    def assets(self) -> List[str]:
        """Parse asset list."""
        return [a.strip() for a in self.asset_list.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
