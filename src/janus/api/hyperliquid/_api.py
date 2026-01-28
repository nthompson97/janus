from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

from ._errors import ClientError, ServerError

MAINNET_API_URL = "https://api.hyperliquid.xyz"
TESTNET_API_URL = "https://api.hyperliquid-testnet.xyz"


class HyperLiquidAPI:
    """Async HyperLiquid API client.

    Usage:
        async with HyperLiquidAPI() as api:
            meta = await api.meta()
            print(meta)
    """

    def __init__(
        self,
        base_url: str = MAINNET_API_URL,
        timeout: float | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout) if timeout else None
        self._session: aiohttp.ClientSession | None = None

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
