import pytest

from janus.core.metadata import BTC, Coin, Perpetual, Spot, USDC


def test_duplicate_coins() -> None:
    with pytest.raises(ValueError):

        class CoinA(Coin):
            name = "foo"

        class CoinB(Coin):
            name = "bar"
            aliases = ["foo"]


def test_get_coin_by_name() -> None:
    assert Coin.from_name("Bitcoin") is BTC
    assert Coin.from_name("USDC") is USDC


def test_get_coin_by_alias() -> None:
    assert Coin.from_name("BTC") is BTC


def test_get_coin_case_insensitive() -> None:
    assert Coin.from_name("bitcoin") is BTC
    assert Coin.from_name("BITCOIN") is BTC
    assert Coin.from_name("btc") is BTC


def test_get_coin_unknown() -> None:
    with pytest.raises(KeyError):
        Coin.from_name("unknown_coin")


def test_spot_creation() -> None:
    spot = BTC / USDC
    assert isinstance(spot, Spot)
    assert spot.base is BTC
    assert spot.quote is USDC


def test_spot_equality() -> None:
    spot1 = Spot(BTC, USDC)
    spot2 = BTC / USDC
    assert spot1 == spot2


def test_spot_inequality() -> None:
    spot1 = BTC / USDC
    spot2 = USDC / BTC
    assert spot1 != spot2


def test_spot_str() -> None:
    spot = BTC / USDC
    assert str(spot) == "BTC/USDC"


def test_spot_repr() -> None:
    spot = BTC / USDC
    assert repr(spot) == "Spot(BTC, USDC)"


def test_perpetual_creation() -> None:
    perp = BTC - USDC
    assert isinstance(perp, Perpetual)
    assert perp.base is BTC
    assert perp.quote is USDC


def test_perpetual_equality() -> None:
    perp1 = Perpetual(BTC, USDC)
    perp2 = BTC - USDC
    assert perp1 == perp2


def test_perpetual_inequality() -> None:
    perp1 = BTC - USDC
    perp2 = USDC - BTC
    assert perp1 != perp2


def test_perpetual_str() -> None:
    perp = BTC - USDC
    assert str(perp) == "BTC-USDC"


def test_perpetual_repr() -> None:
    perp = BTC - USDC
    assert repr(perp) == "Perpetual(BTC, USDC)"


def test_spot_not_equal_to_perpetual() -> None:
    spot = BTC / USDC
    perp = BTC - USDC
    assert spot != perp


def test_spot_not_equal_to_non_spot() -> None:
    spot = BTC / USDC
    assert spot != "BTC/USDC"
    assert spot is not None


def test_perpetual_not_equal_to_non_perpetual() -> None:
    perp = BTC - USDC
    assert perp != "BTC-USDC"
    assert perp is not None
