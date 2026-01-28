from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any
from janus.core.metadata import Coin
import websockets
from websockets import ClientConnection

from ._api import HyperLiquidAPI

MAINNET_WS_URL = "wss://api.hyperliquid.xyz/ws"
TESTNET_WS_URL = "wss://api.hyperliquid-testnet.xyz/ws"


class HyperliquidWebsocket:
    """Async Hyperliquid WebSocket client.

    Usage:
        async with HyperliquidWebsocket() as ws:
            await ws.subscribe_bbo("BTC")
            async for message in ws:
                print(message)
    """

    def __init__(
        self,
        ws_url: str = MAINNET_WS_URL,
    ) -> None:
        self.ws_url = ws_url
        self._ws: ClientConnection | None = None
        self._api = None
        self._subscriptions: list[dict[str, Any]] = []

    async def __aenter__(self) -> HyperliquidWebsocket:
        self._api = HyperLiquidAPI()
        await self._api.__aenter__()

        self._ws = await websockets.connect(self.ws_url)
        logging.info(f"Connected to {self.ws_url}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

        if self._api is not None:
            await self._api.close()
            self._api = None

    @property
    def ws(self) -> ClientConnection:
        if self._ws is None:
            raise RuntimeError(
                "WebSocket not connected. Use 'async with HyperliquidWebsocket()' context manager."
            )
        return self._ws

    @property
    def api(self) -> HyperLiquidAPI:
        if self._api is None:
            raise RuntimeError(
                "API not initialized. Use 'async with HyperliquidWebsocket()' context manager."
            )
        return self._api

    async def send(self, message: dict[str, Any]) -> None:
        await self.ws.send(json.dumps(message))

    async def recv(self) -> dict[str, Any]:
        message = await self.ws.recv()
        return json.loads(message)

    async def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        async for message in self.ws:
            yield json.loads(message)

    async def _subscribe(self, subscription: dict[str, Any]) -> None:
        message = {
            "method": "subscribe",
            "subscription": subscription,
        }
        await self.send(message)

        self._subscriptions.append(subscription)
        logging.info(f"Subscribed: {subscription}")

    async def _unsubscribe(self, subscription: dict[str, Any]) -> None:
        message = {
            "method": "unsubscribe",
            "subscription": subscription,
        }
        await self.send(message)

        if subscription in self._subscriptions:
            self._subscriptions.remove(subscription)

        logging.info(f"Unsubscribed: {subscription}")

    async def subscribe_bbo(self, coin: str) -> None:
        await self._subscribe({"type": "bbo", "coin": coin})
