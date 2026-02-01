import asyncio
import logging
from janus.api.hyperliquid import HyperliquidWebsocket
from janus.core.metadata import BTC, USDC, ETH, SOL
from janus.core.metadata import Perpetual, Spot

LIMIT: int | None = 10

PRODUCTS: list[Perpetual | Spot] = [
    BTC / USDC,  # Spot BTC
    BTC - USDC,  # Perp BTC
    ETH / USDC,  # Spot ETH
    ETH - USDC,  # Perp ETH
]


async def main() -> None:
    async with HyperliquidWebsocket(env="dev") as ws:
        for product in PRODUCTS:
            await ws.subscribe_bbo(product)

        count = 0

        async for message in ws:
            if LIMIT is not None:
                if count > LIMIT:
                    break

            logging.info(message)
            count += 1


if __name__ == "__main__":
    asyncio.run(main())
