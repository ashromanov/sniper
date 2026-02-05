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

### Examples

```bash
# Snipe PEPE with 0.02 SOL
uv run sniper -s PEPE:0.02

# Snipe multiple tokens with different amounts
uv run sniper -s PEPE:0.01 -s DOGE:0.05 -s SHIB:0.1 -s WIF:0.02

# Use default amount from .env for all
uv run sniper -s PEPE -s DOGE -s SHIB
```
