"""Entry point for the Pump.fun sniper service."""

import asyncio
import sys

from loguru import logger

from pumpfun_sniper import config
from pumpfun_sniper.helius_ws import run_websocket
from pumpfun_sniper.pump_portal import PumpPortalClient


def configure_logging() -> None:
    """Configure loguru for structured logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
    )
    logger.add(
        "logs/sniper_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level="INFO",
    )


async def async_main() -> None:
    """Async main entry point."""
    configure_logging()

    logger.info("Starting Pump.fun Sniper")
    logger.info(f"Monitoring {len(config.MONITORED_SYMBOLS)} symbols")
    logger.info(f"Buy amount: {config.BUY_AMOUNT_SOL} SOL")
    logger.info(f"Slippage: {config.SLIPPAGE_PERCENT}%")

    if not config.MONITORED_SYMBOLS:
        logger.warning("No symbols configured in MONITORED_SYMBOLS, will log all creates")

    pump_client = PumpPortalClient()

    try:
        await run_websocket(pump_client)
    finally:
        await pump_client.close()


def main() -> None:
    """Main entry point with uvloop."""
    try:
        import uvloop

        uvloop.install()
        logger.info("Using uvloop")
    except ImportError:
        logger.warning("uvloop not available, using default event loop")

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")


if __name__ == "__main__":
    main()
