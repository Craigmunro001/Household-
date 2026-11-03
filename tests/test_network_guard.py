import httpx
import pytest


def test_a_test_that_tries_to_reach_the_internet_fails_loudly():
    with pytest.raises(Exception) as err:
        httpx.get("https://graph.facebook.com/", timeout=3)
    assert "test" in str(err.value).lower() or "network" in str(err.value).lower() or "dns" in str(err.value).lower()
