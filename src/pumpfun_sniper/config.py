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

# Trading settings
BUY_AMOUNT_SOL: float = float(get_env("BUY_AMOUNT_SOL", "0.01"))
SLIPPAGE_PERCENT: int = int(get_env("SLIPPAGE_PERCENT", "10"))
PRIORITY_FEE: float = float(get_env("PRIORITY_FEE", "0.00005"))

# Monitored token symbols (comma-separated)
_monitored_raw = get_env("MONITORED_SYMBOLS", "")
MONITORED_SYMBOLS: frozenset[str] = frozenset(
    s.strip().upper() for s in _monitored_raw.split(",") if s.strip()
)
