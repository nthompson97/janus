from janus.core.metadata import Coin
import pytest


def test_duplicate_coins() -> None:
    with pytest.raises(ValueError):

        class CoinA(Coin):
            name = "foo"

        class CoinB(Coin):
            name = "bar"
            aliases = ["foo"]


def test_get_coin() -> None:
    class CoinA(Coin):
        name = "foobarbaz"
        aliases = ["Foo, Bar, Baz"]

    coin_0 = Coin.from_name("foobarbaz")
    assert coin_0 is CoinA

    coin_1 = Coin.from_name("Foo, Bar, Baz")
    assert coin_1 is CoinA
