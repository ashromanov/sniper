"""Configuration module for loading environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present
_env_path = Path.cwd() / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def get_env(key: str, default: str | None = None) -> str:
    """Get environment variable or raise if not set and no default.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Environment variable value.

    Raises:
        ValueError: If variable not set and no default provided.
    """
    value = os.getenv(key, default)
    if value is None:
        msg = f"Environment variable {key} is required"
        raise ValueError(msg)
    return value


# Helius API (Enhanced/Geyser WebSocket endpoint)
HELIUS_API_KEY: str = get_env("HELIUS_API_KEY")
HELIUS_WS_URL: str = f"wss://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

# Pump.fun program address
PUMPFUN_PROGRAM_ID: str = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

# PumpPortal API
PUMPPORTAL_API_KEY: str = get_env("PUMPPORTAL_API_KEY")
PUMPPORTAL_BASE_URL: str = "https://pumpportal.fun/api/trade"

# Trading settings (defaults from env, can be overridden via CLI)
BUY_AMOUNT_SOL: float = float(get_env("BUY_AMOUNT_SOL", "0.01"))
SLIPPAGE_PERCENT: int = int(get_env("SLIPPAGE_PERCENT", "10"))
PRIORITY_FEE: float = float(get_env("PRIORITY_FEE", "0.00005"))

# Monitored token symbols (comma-separated, can be overridden via CLI)
_monitored_raw = get_env("MONITORED_SYMBOLS", "")
MONITORED_SYMBOLS: frozenset[str] = frozenset(
    s.strip().upper() for s in _monitored_raw.split(",") if s.strip()
)

# Runtime configuration (set by CLI or programmatically)
_runtime_symbols: frozenset[str] | None = None
_runtime_buy_amounts: dict[str, float] = {}


def set_runtime_symbols(symbols: list[str]) -> None:
    """Set monitored symbols at runtime.
    
    Args:
        symbols: List of token symbols to monitor.
    """
    global _runtime_symbols
    _runtime_symbols = frozenset(s.strip().upper() for s in symbols if s.strip())


def get_monitored_symbols() -> frozenset[str]:
    """Get currently monitored symbols (runtime or config).
    
    Returns:
        Set of monitored symbols.
    """
    return _runtime_symbols if _runtime_symbols is not None else MONITORED_SYMBOLS


def set_buy_amount_for_symbol(symbol: str, amount: float) -> None:
    """Set buy amount for specific symbol.
    
    Args:
        symbol: Token symbol.
        amount: Amount in SOL to buy.
    """
    _runtime_buy_amounts[symbol.upper()] = amount


def get_buy_amount_for_symbol(symbol: str) -> float:
    """Get buy amount for specific symbol.
    
    Args:
        symbol: Token symbol.
        
    Returns:
        Buy amount in SOL.
    """
    return _runtime_buy_amounts.get(symbol.upper(), BUY_AMOUNT_SOL)
