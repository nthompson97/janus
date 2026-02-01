from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any

import aiohttp

from ._errors import ClientError, ServerError
from janus.core.metadata import Coin, Perpetual, Spot, USDC

from ._utils import get_env, get_api_url, HyperliquidEnv


@dataclass()
class ProductMetadata:
    coin: str
    decimals: int


class HyperLiquidAPI:
    """Async HyperLiquid API client.

    Usage:
        async with HyperLiquidAPI() as api:
            meta = await api.meta()
            print(meta)
    """

    def __init__(
        self,
        env: str | HyperliquidEnv = "dev",
        timeout: float | None = None,
    ) -> None:
        self.base_url: str = get_api_url(env)
        self.timeout: aiohttp.ClientTimeout | None = (
            aiohttp.ClientTimeout(total=timeout) if timeout else None
        )
        self._session: aiohttp.ClientSession | None = None

        self._metadata: dict[Perpetual | Spot, ProductMetadata] = dict()

    async def __aenter__(self) -> HyperLiquidAPI:
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def _create_session(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError(
                "Session not initialized. Use 'async with HyperLiquidAPI()' context manager."
            )
        return self._session

    async def post(self, url_path: str, payload: dict[str, Any] | None = None) -> Any:
        """Make an async POST request to the HyperLiquid API.
        NOTE: This has been created by Claude and not vetted by me yet.

        Args:
            url_path: API endpoint path (e.g., "/info").
            payload: JSON payload to send.

        Returns:
            Parsed JSON response.

        Raises:
            ClientError: For 4xx HTTP responses.
            ServerError: For 5xx HTTP responses.
        """
        payload = payload or {}
        url = self.base_url + url_path

        logging.debug("POST %s: %s", url, payload)

        async with self.session.post(url, json=payload) as response:
            await self._handle_exception(response)

            try:
                return await response.json()

            except (json.JSONDecodeError, aiohttp.ContentTypeError):
                text = await response.text()

                return {"error": f"Could not parse JSON: {text}"}

    async def _handle_exception(self, response: aiohttp.ClientResponse) -> None:
        """Handle HTTP error responses.
        NOTE: This has been created by Claude and not vetted by me yet.

        Args:
            response: aiohttp response object.

        Raises:
            ClientError: For 4xx HTTP responses.
            ServerError: For 5xx HTTP responses.
        """
        status_code = response.status

        if status_code < 400:
            return

        text = await response.text()
        headers = dict(response.headers)

        if 400 <= status_code < 500:
            try:
                err = json.loads(text)

            except json.JSONDecodeError:
                raise ClientError(status_code, None, text, headers, None)

            if err is None:
                raise ClientError(status_code, None, text, headers, None)

            error_data = err.get("data")

            raise ClientError(
                status_code,
                err.get("code"),
                err.get("msg", text),
                headers,
                error_data,
            )

        raise ServerError(status_code, text)

    @property
    def metadata(self) -> dict[Perpetual | Spot, ProductMetadata]:
        return self._metadata

    # -------------------------------------------------------------------------
    # Info Endpoints
    # -------------------------------------------------------------------------

    async def meta(self, dex: str = "") -> dict[str, Any]:
        return await self.post(
            "/info",
            {
                "type": "meta",
                "dex": dex,
            },
        )

    async def spot_meta(self) -> dict[str, Any]:
        return await self.post(
            "/info",
            {
                "type": "spotMeta",
            },
        )

    async def meta_and_asset_ctxs(self) -> list[Any]:
        return await self.post(
            "/info",
            {
                "type": "metaAndAssetCtxs",
            },
        )

    async def spot_meta_and_asset_ctxs(self) -> list[Any]:
        return await self.post(
            "/info",
            {
                "type": "spotMetaAndAssetCtxs",
            },
        )

    async def perp_dexs(self) -> list[Any]:
        return await self.post(
            "/info",
            {
                "type": "perpDexs",
            },
        )

    # -------------------------------------------------------------------------
    # Metadata construction
    # -------------------------------------------------------------------------

    async def build_perpetual_metadata(self) -> None:
        meta = await self.meta()

        for i, perpetual in enumerate(meta["universe"]):
            try:
                coin = Coin.from_name(perpetual["name"])

            except KeyError:
                ...

            else:
                # At this stage, all perpetuals are crossed with USDC
                self._metadata[Perpetual(coin, USDC)] = ProductMetadata(
                    coin=perpetual["name"],
                    decimals=perpetual["szDecimals"],
                )
                logging.info(f"Added metadata for {coin}-USDC")

    async def build_spot_metadata(self) -> None:
        # TODO: I'm unsure yet if this should live here or on the actual coin metadata
        # TODO: there are are few options for XRP, need to add the right mapping here
        l1_mapping = {
            "UBTC": "BTC",
            "UETH": "ETH",
            "USOL": "SOL",
        }
        meta = await self.spot_meta()

        index_map = {
            i["index"]: (l1_mapping.get(i["name"], i["name"]), i["szDecimals"])
            for i in meta["tokens"]
        }

        for i, spot in enumerate(meta["universe"]):
            base_idx, quote_idx = spot["tokens"]
            base, quote = index_map[base_idx], index_map[quote_idx]

            try:
                base_coin = Coin.from_name(base[0])
                quote_coin = Coin.from_name(quote[0])

            except KeyError:
                ...

            else:
                self._metadata[Spot(base_coin, quote_coin)] = ProductMetadata(
                    coin=spot["name"],
                    decimals=base[1],
                )
                logging.info(f"Added metadata for {base_coin}/{quote_coin}")
