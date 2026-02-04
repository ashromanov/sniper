# Pump.fun Token Sniper

Python service that monitors Solana Pump.fun token creations via Helius Geyser Enhanced WebSockets and automatically buys matching tokens.

## See for yourself
![ConsoleOverview](/screenshots/ConsoleOverview.png)

---

![FoundExample](/screenshots/FoundExample.png)

## Requirements

- Python 3.13+
- [Helius API Key](https://www.helius.dev/)
- [PumpPortal API Key](https://pumpportal.fun/)

## Installation

```bash
cd sniper

uv sync

cp .env.example .env

```

## Usage

```bash
uv run sniper

uv run python -m pumpfun_sniper
```
