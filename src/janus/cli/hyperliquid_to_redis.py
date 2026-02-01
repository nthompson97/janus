import argparse
import asyncio
import logging
import time
from typing import Any, Literal

import redis.asyncio as redis

from janus.api.hyperliquid import HyperliquidWebsocket
from janus.core.metadata import BTC, USDC, ETH, SOL, HYPE
from janus.core.metadata import Perpetual, Spot

Side = Literal["bid", "ask"]

PRODUCTS: list[Perpetual | Spot] = [
    BTC / USDC,  # Spot BTC
    BTC - USDC,  # Perp BTC
    ETH / USDC,  # Spot ETH
    ETH - USDC,  # Perp ETH
    SOL / USDC,  # Spot SOL
    SOL - USDC,  # Perp SOL
    HYPE - USDC,  # Perp HYPE
]


def get_redis_key(product: Perpetual | Spot, side: Side) -> str:
    """Generate Redis TimeSeries key for a product and side.

    Args:
        product: The product (Perpetual or Spot)
        side: Either 'bid' or 'ask'

    Returns:
        Key like 'hyperliquid:bbo:BTC-USDC:bid' or 'hyperliquid:bbo:BTC/USDC:ask'
    """
    return f"hyperliquid:bbo:{product}:{side}"


async def ensure_timeseries(
    redis_client: redis.Redis,
    key: str,
    retention_ms: int = 60 * 60 * 24 * 1000,
) -> None:
    """Create a TimeSeries key if it doesn't exist.

    Args:
        redis_client: Async Redis client
        key: The TimeSeries key to create
        retention_ms: Data retention period in milliseconds
    """
    try:
        await redis_client.execute_command("TS.CREATE", key, "RETENTION", retention_ms)
        logging.info(f"Created TimeSeries: {key}")

    except redis.ResponseError as e:
        if "already exists" in str(e).lower():
            logging.debug(f"TimeSeries already exists: {key}")

        else:
            raise


async def push_bbo_to_redis(
    redis_client: redis.Redis,
    product: Perpetual | Spot,
    bid_price: float,
    ask_price: float,
    timestamp_ms: int | None = None,
) -> None:
    """Push BBO prices to Redis TimeSeries.

    Args:
        redis_client: Async Redis client
        product: The product being updated
        bid_price: Best bid price
        ask_price: Best ask price
        timestamp_ms: Timestamp in milliseconds (uses current time if None)
    """
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)

    bid_key = get_redis_key(product, "bid")
    ask_key = get_redis_key(product, "ask")

    await redis_client.execute_command("TS.ADD", bid_key, timestamp_ms, bid_price)
    await redis_client.execute_command("TS.ADD", ask_key, timestamp_ms, ask_price)


def parse_bbo_message(message: dict[str, Any]) -> tuple[str, float, float, int] | None:
    """Parse a BBO websocket message.

    Args:
        message: Raw websocket message

    Returns:
        Tuple of (coin, bid_price, ask_price, timestamp_ms) or None if not a BBO message
    """
    if message.get("channel") != "bbo":
        return None

    data = message.get("data", {})
    coin = data.get("coin")

    if not coin:
        return None

    bid_data = data.get("bbo", [[None, None], [None, None]])

    # BBO format: [[bid_px, bid_sz], [ask_px, ask_sz]]
    try:
        bid_price = float(bid_data[0][0]) if bid_data[0][0] else None
        ask_price = float(bid_data[1][0]) if bid_data[1][0] else None
    except (IndexError, TypeError, ValueError):
        logging.warning(f"Failed to parse BBO data: {bid_data}")
        return None

    if bid_price is None or ask_price is None:
        return None

    # Use current time as timestamp (Hyperliquid BBO doesn't include timestamp)
    timestamp_ms = int(time.time() * 1000)

    return coin, bid_price, ask_price, timestamp_ms


async def run_service(
    redis_url: str = "redis://localhost:6379",
    env: str = "dev",
    retention_hours: int = 24,
) -> None:
    """Run the BBO to Redis service.

    Args:
        redis_url: Redis connection URL
        env: Hyperliquid environment ('dev' or 'prod')
        retention_hours: How long to retain TimeSeries data in hours
    """
    redis_client = redis.from_url(redis_url)
    retention_ms = retention_hours * 60 * 60 * 1000

    logging.info(f"Connecting to Redis at {redis_url}")
    await redis_client.ping()
    logging.info("Redis connection established")

    async with HyperliquidWebsocket(env=env) as ws:
        # Build a mapping from coin name to product for Redis key generation
        coin_to_product: dict[str, Perpetual | Spot] = {}

        for product in PRODUCTS:
            metadata = ws.api.metadata.get(product)
            if metadata:
                coin_to_product[metadata.coin] = product
                logging.info(f"Mapped {metadata.coin} -> {product}")

        # Subscribe to all products
        for product in PRODUCTS:
            try:
                await ws.subscribe_bbo(product)
            except ValueError as e:
                logging.warning(f"Could not subscribe to {product}: {e}")

        # Create TimeSeries keys
        for product in coin_to_product.values():
            await ensure_timeseries(
                redis_client, get_redis_key(product, "bid"), retention_ms
            )
            await ensure_timeseries(
                redis_client, get_redis_key(product, "ask"), retention_ms
            )

        logging.info("Starting BBO stream processing...")
        message_count = 0

        async for message in ws:
            parsed = parse_bbo_message(message)

            if parsed is None:
                continue

            coin, bid_price, ask_price, timestamp_ms = parsed
            product = coin_to_product.get(coin)

            if product is None:
                logging.debug(f"Unknown coin in message: {coin}")
                continue

            await push_bbo_to_redis(
                redis_client, product, bid_price, ask_price, timestamp_ms
            )

            message_count += 1
            if message_count % 100 == 0:
                logging.info(f"Processed {message_count} BBO updates")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream Hyperliquid BBO data to Redis TimeSeries"
    )
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379",
        help="Redis connection URL (default: redis://localhost:6379)",
    )
    parser.add_argument(
        "--env",
        choices=["dev", "prod"],
        default="dev",
        help="Hyperliquid environment (default: dev)",
    )
    parser.add_argument(
        "--retention-hours",
        type=int,
        default=24,
        help="TimeSeries retention period in hours (default: 24)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        asyncio.run(
            run_service(
                redis_url=args.redis_url,
                env=args.env,
                retention_hours=args.retention_hours,
            )
        )

    except KeyboardInterrupt:
        logging.info("Service stopped by user")


if __name__ == "__main__":
    main()
