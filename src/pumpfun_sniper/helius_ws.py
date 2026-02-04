"""Helius Geyser Enhanced WebSocket client using picows."""

import asyncio
import base64
import struct

import msgspec
from loguru import logger
from picows import WSFrame, WSListener, WSMsgType, WSTransport, ws_connect

from pumpfun_sniper import config
from pumpfun_sniper.decorators import timed
from pumpfun_sniper.models import WebSocketMessage
from pumpfun_sniper.pump_portal import PumpPortalClient

# Log prefix for Pump.fun CreateEvent data
PROGRAM_DATA_PREFIX = "Program data: "
# CreateEvent discriminator (first 8 bytes)
CREATE_EVENT_DISCRIMINATOR = bytes([27, 114, 169, 77, 222, 235, 99, 118])


class HeliusWSListener(WSListener):
    """WebSocket listener for Helius Geyser Enhanced WebSockets."""

    def __init__(
        self,
        pump_client: PumpPortalClient,
        monitored_symbols: frozenset[str],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Initialize listener.

        Args:
            pump_client: PumpPortal client for trading.
            monitored_symbols: Set of token symbols to monitor.
            loop: Event loop for scheduling async tasks.
        """
        self._pump_client = pump_client
        self._monitored_symbols = monitored_symbols
        self._loop = loop
        self._decoder = msgspec.json.Decoder(WebSocketMessage)
        self._transport: WSTransport | None = None
        self.disconnected = asyncio.Event()
        self._ping_task: asyncio.Task | None = None

    def on_ws_connected(self, transport: WSTransport) -> None:
        """Handle WebSocket connection established."""
        self._transport = transport
        logger.info("WebSocket connected to Helius")
        self._subscribe()
        # Start ping task to keep connection alive (Helius requires ping every 10s)
        self._ping_task = self._loop.create_task(self._ping_loop())

    def _subscribe(self) -> None:
        """Send subscription request for Pump.fun transactions."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "transactionSubscribe",
            "params": [
                {
                    "failed": False,
                    "accountInclude": [config.PUMPFUN_PROGRAM_ID],
                },
                {
                    "commitment": "confirmed",
                    "encoding": "jsonParsed",
                    "transactionDetails": "full",
                    "maxSupportedTransactionVersion": 0,
                },
            ],
        }
        payload = msgspec.json.encode(request)
        if self._transport:
            self._transport.send(WSMsgType.TEXT, payload)
            logger.info(f"Subscribed to Pump.fun program: {config.PUMPFUN_PROGRAM_ID}")

    def on_ws_frame(self, transport: WSTransport, frame: WSFrame) -> None:
        """Handle incoming WebSocket frame."""
        if frame.msg_type != WSMsgType.TEXT:
            return

        try:
            self._process_message(frame.get_payload_as_memoryview())
        except Exception as e:
            logger.exception(f"Error processing message: {e}")

    @timed
    def _process_message(self, data: memoryview) -> None:
        """Process incoming WebSocket message.

        Args:
            data: Raw message bytes.
        """
        try:
            msg = self._decoder.decode(data)
        except msgspec.DecodeError:
            # Subscription confirmation or other non-transaction messages
            logger.debug(f"Non-parseable message: {bytes(data)[:200]}")
            return

        # Subscription confirmation
        if msg.result is not None and msg.params is None:
            logger.info(f"Subscription confirmed, ID: {msg.result}")
            return

        if msg.params is None:
            return

        result = msg.params.result
        tx_meta = result.transaction.meta
        signature = result.signature

        # Check for errors
        if tx_meta.err is not None:
            return

        logs = tx_meta.logMessages or []

        # Try to decode CreateEvent from "Program data:" log
        token_info = self._decode_create_event(logs)
        if token_info is None:
            return

        mint, name, symbol, uri, bonding_curve, creator = token_info

        logger.info(
            f"New token created | Tx: {signature} | Symbol: {symbol} | "
            f"Name: {name} | Mint: {mint} | Creator: {creator}"
        )

        # Check if symbol is in monitored set
        if symbol.upper() not in self._monitored_symbols:
            logger.debug(f"Symbol {symbol} not in monitored set, skipping")
            return

        logger.success(f"Symbol {symbol} MATCHED! Initiating buy for {mint}")
        self._loop.create_task(self._execute_buy(mint, symbol))

    def _decode_create_event(
        self, logs: list[str]
    ) -> tuple[str, str, str, str, str, str] | None:
        """Decode CreateEvent from Program data log.

        Args:
            logs: List of log messages from transaction.

        Returns:
            Tuple of (mint, name, symbol, uri, bonding_curve, user) or None.
        """
        for log in logs:
            if not log.startswith(PROGRAM_DATA_PREFIX):
                continue

            b64_data = log[len(PROGRAM_DATA_PREFIX) :]
            try:
                data = base64.b64decode(b64_data)
            except Exception:
                continue

            # Check minimum size and discriminator (first 8 bytes)
            # Minimum size: 8 (disc) + 12 (3 empty strings) + 96 (3 pubkeys) = 116
            if len(data) < 100:
                continue
            
            if data[:8] != CREATE_EVENT_DISCRIMINATOR:
                continue

            # Parse the CreateEvent structure.
            # Based on observation, the layout seems to be:
            # 8 bytes: discriminator
            # String: name
            # String: symbol
            # String: uri
            # 32 bytes: mint
            # 32 bytes: bonding_curve
            # 32 bytes: user
            try:
                offset = 8
                
                # Read length-prefixed strings first
                name, offset = self._read_string(data, offset)
                symbol, offset = self._read_string(data, offset)
                uri, offset = self._read_string(data, offset)

                # Then read pubkeys
                if offset + 32 > len(data):
                    raise ValueError(f"Not enough data for mint at {offset}")
                mint = self._bytes_to_pubkey(data[offset : offset + 32])
                offset += 32

                if offset + 32 > len(data):
                    raise ValueError(f"Not enough data for bonding_curve at {offset}")
                bonding_curve = self._bytes_to_pubkey(data[offset : offset + 32])
                offset += 32

                if offset + 32 > len(data):
                    raise ValueError(f"Not enough data for user at {offset}")
                user = self._bytes_to_pubkey(data[offset : offset + 32])
                offset += 32

                return (mint, name, symbol, uri, bonding_curve, user)

            except Exception as e:
                # If that fails, log hex for debugging
                logger.debug(f"Failed to decode CreateEvent: {e}")
                if len(data) > 8:
                    logger.debug(f"Hex dump: {data.hex()[:200]}...")
                continue

        return None

    @staticmethod
    def _bytes_to_pubkey(data: bytes) -> str:
        """Convert 32 bytes to base58 pubkey string."""
        # Simple base58 encoding for Solana pubkeys
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        num = int.from_bytes(data, "big")
        result = []
        while num:
            num, rem = divmod(num, 58)
            result.append(alphabet[rem])
        # Handle leading zeros
        for byte in data:
            if byte == 0:
                result.append("1")
            else:
                break
        return "".join(reversed(result))

    @staticmethod
    def _read_string(data: bytes, offset: int) -> tuple[str, int]:
        """Read a length-prefixed string from data.

        Args:
            data: Raw bytes.
            offset: Current offset.

        Returns:
            Tuple of (string, new_offset).

        Raises:
            ValueError: If string length is invalid or exceeds buffer.
        """
        if offset + 4 > len(data):
            raise ValueError(f"Not enough data for length prefix at offset {offset}")
        
        (length,) = struct.unpack_from("<I", data, offset)
        offset += 4
        
        # Sanity check: string length should be reasonable (< 1000 chars)
        if length > 1000 or offset + length > len(data):
            raise ValueError(
                f"Invalid string length {length} at offset {offset - 4}, "
                f"buffer size {len(data)}"
            )
        
        string = data[offset : offset + length].decode("utf-8", errors="replace")
        return string, offset + length

    async def _execute_buy(self, mint: str, symbol: str) -> None:
        """Execute buy order for token.

        Args:
            mint: Token mint address.
            symbol: Token symbol.
        """
        await self._pump_client.buy_token(mint, symbol)

    async def _ping_loop(self) -> None:
        """Send periodic pings to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(10)
                if self._transport:
                    self._transport.send_ping(b"")
        except asyncio.CancelledError:
            pass

    def on_ws_closed(self, code: int, reason: bytes) -> None:
        """Handle WebSocket connection closed."""
        logger.warning(f"WebSocket closed: {code} {reason!r}")
        if self._ping_task:
            self._ping_task.cancel()
        self.disconnected.set()

    def on_ws_ping(self, transport: WSTransport, data: bytes) -> None:
        """Handle ping, respond with pong."""
        transport.send_pong(data)


async def run_websocket(pump_client: PumpPortalClient) -> None:
    """Run the Helius WebSocket connection.

    Args:
        pump_client: PumpPortal client for executing trades.
    """
    loop = asyncio.get_running_loop()

    logger.info("Connecting to Helius WebSocket...")
    logger.info(f"Monitoring symbols: {sorted(config.MONITORED_SYMBOLS)}")

    while True:
        listener = HeliusWSListener(pump_client, config.MONITORED_SYMBOLS, loop)
        try:
            transport, _ = await ws_connect(lambda: listener, config.HELIUS_WS_URL)

            # Wait for disconnection
            await listener.disconnected.wait()

        except Exception as e:
            logger.exception(f"WebSocket error: {e}")

        logger.info("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)
