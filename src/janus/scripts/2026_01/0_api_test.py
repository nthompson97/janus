import asyncio
from janus.api.hyperliquid import HyperLiquidAPI


async def main() -> None:
    async with HyperLiquidAPI() as api:
        spot_meta = await api.spot_meta()

        coin_to_asset = {}
        name_to_coin = {}
        asset_to_sz_decimals = {}

        for i, spot in enumerate(spot_meta["universe"]):
            name = spot["name"]
            asset = spot["index"] + 10000

            base, quote = spot["tokens"]

            base_info = spot_meta["tokens"][base]
            quote_info = spot_meta["tokens"][quote]

            coin_to_asset[name] = asset
            name_to_coin[name] = name
            asset_to_sz_decimals[asset] = base_info["szDecimals"]

        # add the perpetuals in
        meta = await api.meta()

        for asset, asset_info in enumerate(meta["universe"]):
            coin_to_asset[asset_info["name"]] = asset
            name_to_coin[asset_info["name"]] = asset_info["name"]
            asset_to_sz_decimals[asset] = asset_info["szDecimals"]

    return spot_meta, meta, coin_to_asset, name_to_coin, asset_to_sz_decimals


if __name__ == "__main__":
    spot_meta, meta, coin_to_asset, name_to_coin, asset_to_sz_decimals = asyncio.run(
        main()
    )

    from IPython import embed

    embed()
