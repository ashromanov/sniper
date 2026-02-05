"""Entry point for the Pump.fun sniper service."""

import asyncio
import sys

import typer
from loguru import logger

from pumpfun_sniper import config
from pumpfun_sniper.helius_ws import run_websocket
from pumpfun_sniper.pump_portal import PumpPortalClient

app = typer.Typer()


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


async def async_main(symbols: list[str], amounts: dict[str, float]) -> None:
    """Async main entry point.
    
    Args:
        symbols: List of symbols to monitor.
        amounts: Dict mapping symbols to buy amounts.
    """
    configure_logging()

    # Set runtime configuration
    if symbols:
        config.set_runtime_symbols(symbols)
        for symbol, amount in amounts.items():
            config.set_buy_amount_for_symbol(symbol, amount)

    monitored = config.get_monitored_symbols()
    
    logger.info("Starting Pump.fun Sniper")
    logger.info(f"Monitoring {len(monitored)} symbols: {sorted(monitored)}")
    
    # Log buy amounts per symbol
    for symbol in sorted(monitored):
        amount = config.get_buy_amount_for_symbol(symbol)
        logger.info(f"  {symbol}: {amount} SOL")
    
    logger.info(f"Slippage: {config.SLIPPAGE_PERCENT}%")
    logger.info(f"Priority fee: {config.PRIORITY_FEE} SOL")

    if not monitored:
        logger.warning("No symbols configured, will log all creates")

    pump_client = PumpPortalClient()

    try:
        await run_websocket(pump_client)
    finally:
        await pump_client.close()


@app.command()
def run(
    symbols: list[str] = typer.Option(
        None,
        "--symbol",
        "-s",
        help="Token symbol to monitor (can be specified multiple times). Format: SYMBOL or SYMBOL:AMOUNT",
    ),
) -> None:
    """Run the Pump.fun sniper.
    
    Examples:
        sniper run -s PEPE -s DOGE:0.05 -s SHIB:0.1
        sniper run --symbol PEPE:0.02
    """
    # Parse symbols and amounts
    parsed_symbols = []
    amounts = {}
    
    if symbols:
        for spec in symbols:
            if ":" in spec:
                symbol, amount_str = spec.split(":", 1)
                try:
                    amount = float(amount_str)
                    parsed_symbols.append(symbol)
                    amounts[symbol] = amount
                except ValueError:
                    typer.echo(f"Invalid amount for {symbol}: {amount_str}", err=True)
                    raise typer.Exit(1)
            else:
                parsed_symbols.append(spec)
    
    # Setup uvloop
    try:
        import uvloop
        uvloop.install()
        logger.info("Using uvloop")
    except ImportError:
        pass

    try:
        asyncio.run(async_main(parsed_symbols, amounts))
    except KeyboardInterrupt:
        logger.info("Shutdown requested")


def main() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
