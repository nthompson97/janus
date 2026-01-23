import asyncio
from janus.api.hyperliquid import HyperLiquidAPI
import nest_asyncio


async def main() -> None:
    async with HyperLiquidAPI() as api:
        meta = await api.spot_meta()
        print(meta)

        from IPython import embed

        embed(using="asyncio")

        # xxx


if __name__ == "__main__":
    nest_asyncio.apply()

    asyncio.run(main())
