"""Async tests for perlthon."""

import asyncio

import pytest

import perlthon


def define_test_functions() -> None:
    perlthon.eval(
        "package Async::Math;"
        "sub add { my ($left, $right) = @_; return $left + $right; };"
        "sub multiply { my ($left, $right) = @_; return $left * $right; };"
        "sub increment { my ($class, $value) = @_; return $value + 1; };"
        "1;"
    )


@pytest.mark.asyncio
async def test_async_eval_returns_correct_values():
    result = await perlthon.async_eval("2 + 2")
    assert result == 4


@pytest.mark.asyncio
async def test_async_call_works_with_arguments():
    define_test_functions()
    result = await perlthon.async_call("Async::Math::add", 20, 22)
    assert result == 42


@pytest.mark.asyncio
async def test_async_use_loads_modules():
    posix = await perlthon.async_use("POSIX")
    assert posix.floor(3.75) == 3.0


@pytest.mark.asyncio
async def test_perl_module_acall_works():
    define_test_functions()
    module = perlthon.PerlModule("Async::Math")
    result = await module.acall("increment", 41)
    assert result == 42


@pytest.mark.asyncio
async def test_multiple_concurrent_async_operations():
    define_test_functions()
    module = perlthon.PerlModule("Async::Math")

    results = await asyncio.gather(
        perlthon.async_eval("[map { $_ ** 2 } 1..4]"),
        perlthon.async_call("Async::Math::multiply", 6, 7),
        module.acall("increment", 41),
        *(perlthon.async_eval(f"{value} + {value}") for value in range(3)),
    )

    assert results == [[1, 4, 9, 16], 42, 42, 0, 2, 4]


@pytest.mark.asyncio
async def test_async_errors_propagate():
    with pytest.raises(RuntimeError, match="boom"):
        await perlthon.async_eval('die "boom"')


@pytest.mark.asyncio
async def test_async_eval_handles_complex_data_types():
    result = await perlthon.async_eval(
        "do { +{"
        "answer => 42,"
        "nested => [1, { two => 2 }, [3, 4]],"
        'message => "hello",'
        "nothing => undef,"
        "} }"
    )

    assert result == {
        "answer": 42,
        "nested": [1, {"two": 2}, [3, 4]],
        "message": "hello",
        "nothing": None,
    }
