import enum


class HyperliquidEnv(enum.Enum):
    Dev = "dev"
    Prod = "prod"


def get_env(env: str | HyperliquidEnv) -> HyperliquidEnv:
    if isinstance(env, str):
        assert env.lower() in {"dev", "prod"}
        return HyperliquidEnv(env.lower())

    elif isinstance(env, HyperliquidEnv):
        return env

    else:
        raise ValueError(f"Unrecognised environment: {env}")


def get_api_url(env: str | HyperliquidEnv) -> str:
    env = get_env(env)

    match env:
        case HyperliquidEnv.Prod:
            return "https://api.hyperliquid.xyz"

        case HyperliquidEnv.Dev:
            return "https://api.hyperliquid-testnet.xyz"

        case _:
            raise ValueError(f"Unrecognised environment: {env}")


def get_ws_url(env: str | HyperliquidEnv) -> str:
    env = get_env(env)

    match env:
        case HyperliquidEnv.Prod:
            return "wss://api.hyperliquid.xyz/ws"

        case HyperliquidEnv.Dev:
            return "wss://api.hyperliquid-testnet.xyz/ws"

        case _:
            raise ValueError(f"Unrecognised environment: {env}")
