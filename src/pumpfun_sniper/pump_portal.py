"""PumpPortal API client for executing trades."""

import aiohttp
import msgspec
from loguru import logger

from pumpfun_sniper import config
from pumpfun_sniper.decorators import async_timed
from pumpfun_sniper.models import TradeResponse


class PumpPortalClient:
    """Async client for PumpPortal trading API."""

    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize client.

        Args:
            session: Optional aiohttp session to reuse.
        """
        self._session = session
        self._owns_session = session is None
        self._encoder = msgspec.json.Encoder()
        self._decoder = msgspec.json.Decoder(TradeResponse)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close session if owned."""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    @async_timed
    async def buy_token(
        self, mint: str, symbol: str, amount_sol: float | None = None
    ) -> TradeResponse | None:
        """Buy a token on Pump.fun.

        Args:
            mint: Token mint address (contract address).
            symbol: Token symbol for logging.
            amount_sol: Amount in SOL to buy. If None, uses config default.

        Returns:
            Trade response or None on failure.
        """
        url = f"{config.PUMPPORTAL_BASE_URL}?api-key={config.PUMPPORTAL_API_KEY}"
        session = await self._get_session()

        # Build form data directly without intermediate model
        data = {
            "action": "buy",
            "mint": mint,
            "amount": amount_sol if amount_sol is not None else config.BUY_AMOUNT_SOL,
            "denominatedInSol": "true",
            "slippage": config.SLIPPAGE_PERCENT,
            "priorityFee": config.PRIORITY_FEE,
            "pool": "pump",
        }

        try:
            async with session.post(url, data=data) as resp:
                body = await resp.read()

                if resp.status != 200:
                    logger.error(
                        f"Buy request failed for {symbol}: HTTP {resp.status} - {body.decode()}"
                    )
                    return None

                response = self._decoder.decode(body)

                if response.error or response.errors:
                    errors = response.error or ", ".join(response.errors or [])
                    logger.error(f"Buy failed for {symbol}: {errors}")
                    return response

                logger.success(
                    f"Buy executed for {symbol} | Mint: {mint} | Tx: {response.signature}"
                )
                return response

        except aiohttp.ClientError as e:
            logger.exception(f"HTTP error buying {symbol}: {e}")
            return None
        except msgspec.DecodeError as e:
            logger.exception(f"Failed to decode response for {symbol}: {e}")
            return None
