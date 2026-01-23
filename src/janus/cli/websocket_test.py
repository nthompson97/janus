import asyncio
import json
import logging

import websockets

from janus.core.metadata import Coin, BTC, ETH

TIMEOUT = 3
MAX_COUNT = 10

# WS_URL = "wss://api.hyperliquid.xyz/ws"  # prod
WS_URL = "wss://api.hyperliquid-testnet.xyz/ws"  # testnet


COINS = [
    BTC,
    ETH,
]


async def subscribe_bbo(ws: websockets.ClientConnection, coin: type[Coin]) -> None:
    msg = {
        "method": "subscribe",
        "subscription": {"type": "bbo", "coin": coin.name},
    }

    await ws.send(json.dumps(msg))
    logging.info(f"Subscribed to BBO for {coin}")


async def main() -> None:
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                logging.info(f"Connected to {WS_URL}")

                for coin in COINS:
                    await subscribe_bbo(ws, coin=coin)

                count = 0

                async for message in ws:
                    data = json.loads(message)

                    logging.info(f"Iteration {count}")
                    logging.info(message)
                    logging.info(data)

                    count += 1

                    if count > MAX_COUNT:
                        break

                break

        except Exception as e:
            logging.error(f"Disconnect from {WS_URL}")
            logging.error(e)

            logging.info(f"Retrying in {TIMEOUT} seconds")
            await asyncio.sleep(TIMEOUT)


if __name__ == "__main__":
    asyncio.run(main())
