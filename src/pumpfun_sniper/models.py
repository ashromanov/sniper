"""Data models for parsing WebSocket and API responses using msgspec."""

import msgspec


class AccountKey(msgspec.Struct, frozen=True):
    """Account key in transaction message."""

    pubkey: str
    signer: bool = False
    writable: bool = False
    source: str = ""


class TransactionMessage(msgspec.Struct, frozen=True):
    """Transaction message containing account keys."""

    accountKeys: list[AccountKey]


class Transaction(msgspec.Struct, frozen=True):
    """Inner transaction object."""

    message: TransactionMessage


class TransactionMeta(msgspec.Struct, frozen=True):
    """Transaction metadata with logs."""

    logMessages: list[str] | None = None
    err: dict | None = None


class TransactionWrapper(msgspec.Struct, frozen=True):
    """Wrapper containing transaction and meta."""

    transaction: Transaction
    meta: TransactionMeta


class TransactionResult(msgspec.Struct, frozen=True):
    """Result object from WebSocket message."""

    signature: str
    transaction: TransactionWrapper


class Params(msgspec.Struct, frozen=True):
    """Params object containing result."""

    result: TransactionResult


class WebSocketMessage(msgspec.Struct, frozen=True):
    """Top-level WebSocket message structure."""

    jsonrpc: str = "2.0"
    method: str | None = None
    params: Params | None = None
    id: int | None = None
    result: int | None = None  # Subscription confirmation


class TradeRequest(msgspec.Struct, frozen=True):
    """Request body for PumpPortal trade API."""

    action: str
    mint: str
    amount: float
    denominatedInSol: str
    slippage: int
    priorityFee: float
    pool: str = "pump"


class TradeResponse(msgspec.Struct, frozen=True, kw_only=True):
    """Response from PumpPortal trade API."""

    signature: str | None = None
    status: str | None = None
    error: str | None = None
    errors: list[str] | None = None
