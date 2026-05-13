"""Perlthon: Import and run Perl modules from Python."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from perlthon._core import PerlInterpreter as _PerlInterpreter
from perlthon._core import hello_from_bin

# Type alias for values returned from Perl
type PerlValue = str | int | float | bool | list[Any] | dict[str, Any] | None

__all__ = [
    "PerlCallable",
    "PerlModule",
    "PerlValue",
    "async_call",
    "async_eval",
    "async_use",
    "call",
    "eval",
    "hello",
    "use",
]

_interpreter: _PerlInterpreter | None = None
_interpreter_lock = threading.RLock()
_executor = ThreadPoolExecutor(thread_name_prefix="perlthon")


def hello() -> str:
    return hello_from_bin()


async def _run_async(
    func: Callable[..., PerlValue | PerlModule], *args: object
) -> PerlValue | PerlModule:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, func, *args)


def _get_interpreter() -> _PerlInterpreter:
    global _interpreter
    with _interpreter_lock:
        if _interpreter is None:
            _interpreter = _PerlInterpreter()
        return _interpreter


class PerlModule:
    """A loaded Perl module, supporting attribute-based method calls."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._interp = _get_interpreter()

    def __repr__(self) -> str:
        return f"PerlModule({self._name!r})"

    def __getattr__(self, name: str) -> PerlCallable:
        return PerlCallable(self._interp, self._name, name)

    def call(self, method: str, *args: object) -> PerlValue:
        """Call a method on this Perl module (OO-style, passes module as invocant)."""
        with _interpreter_lock:
            return self._interp.call_method(self._name, method, list(args))

    async def acall(self, method: str, *args: object) -> PerlValue:
        """Asynchronously call a method on this Perl module."""
        return await _run_async(self.call, method, *args)


class PerlCallable:
    """A lazy reference to a Perl function/method, callable from Python.

    By default, calls the function using its fully qualified name
    (e.g. ``POSIX::floor``). For OO-style method dispatch, use
    ``module.call("method", ...)``.
    """

    def __init__(self, interp: _PerlInterpreter, module: str, method: str) -> None:
        self._interp = interp
        self._module = module
        self._method = method

    def __repr__(self) -> str:
        return f"PerlCallable({self._module}::{self._method})"

    def __call__(self, *args: object) -> PerlValue:
        fqn = f"{self._module}::{self._method}"
        with _interpreter_lock:
            return self._interp.call_function(fqn, list(args))


def use(module_name: str) -> PerlModule:
    """Load a Perl module (equivalent to Perl's ``use Module``).

    Args:
        module_name: Fully qualified Perl module name (e.g. ``"Text::CSV"``).

    Returns:
        A :class:`PerlModule` proxy that supports method calls.
    """
    with _interpreter_lock:
        interp = _get_interpreter()
        interp.use_module(module_name)
        return PerlModule(module_name)


async def async_eval(code: str) -> PerlValue:
    """Evaluate Perl code without blocking the current event loop."""
    return await _run_async(eval, code)


async def async_call(function_name: str, *args: object) -> PerlValue:
    """Call a Perl function without blocking the current event loop."""
    return await _run_async(call, function_name, *args)


async def async_use(module_name: str) -> PerlModule:
    """Load a Perl module without blocking the current event loop."""
    result = await _run_async(use, module_name)
    return result


def call(function_name: str, *args: object) -> PerlValue:
    """Call a Perl function by its fully qualified name.

    Args:
        function_name: E.g. ``"POSIX::floor"``.
        *args: Arguments to pass to the Perl function.

    Returns:
        The return value from Perl, converted to a Python type.
    """
    with _interpreter_lock:
        interp = _get_interpreter()
        return interp.call_function(function_name, list(args))


def eval(code: str) -> PerlValue:
    """Evaluate a string of Perl code and return the result.

    Args:
        code: Perl source code to evaluate.

    Returns:
        The result of the evaluation, converted to a Python type.
    """
    with _interpreter_lock:
        interp = _get_interpreter()
        return interp.eval(code)
