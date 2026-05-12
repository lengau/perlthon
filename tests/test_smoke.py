"""Smoke tests for perlthon."""

import perlthon


def test_hello():
    result = perlthon.hello()
    assert isinstance(result, str)
    assert "perlthon" in result.lower()
