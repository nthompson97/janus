import enum


class HyperliquidEnvironment(enum.Enum):
    Dev = enum.auto()
    Prod = enum.auto()


def get_env(env: str | HyperliquidEnvironment) -> HyperliquidEnvironment:
    if isinstance(env, str):
        assert env.lower() in {"dev", "prod"}
        return HyperliquidEnvironment(env.lower())

    elif isinstance(env, HyperliquidEnvironment):
        return env

    else:
        raise ValueError(f"Unrecognised environment: {env}")


def get_api_url(env: HyperliquidEnvironment) -> str:
    match env:
        case HyperliquidEnvironment.Prod:
            return "https://api.hyperliquid.xyz"

        case HyperliquidEnvironment.Dev:
            return "https://api.hyperliquid-testnet.xyz"

        case _:
            raise ValueError(f"Unrecognised environment: {env}")


def get_ws_url(env: HyperliquidEnvironment) -> str:
    match env:
        case HyperliquidEnvironment.Prod:
            return "wss://api.hyperliquid.xyz/ws"

        case HyperliquidEnvironment.Dev:
            return "wss://api.hyperliquid-testnet.xyz/ws"

        case _:
            raise ValueError(f"Unrecognised environment: {env}")
