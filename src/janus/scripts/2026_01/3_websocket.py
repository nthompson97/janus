import asyncio
import logging
from janus.api.hyperliquid import HyperliquidWebsocket

LIMIT = 10


async def main() -> None:
    async with HyperliquidWebsocket() as ws:
        await ws.subscribe_bbo("BTC")
        await ws.subscribe_bbo("ETH")

        count = 0

        async for message in ws:
            if LIMIT is not None:
                if count > LIMIT:
                    break

            logging.info(message)
            count += 1


if __name__ == "__main__":
    asyncio.run(main())
