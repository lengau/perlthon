"""Perlthon: Import and run Perl modules from Python."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from typing import TYPE_CHECKING, Any

from perlthon._core import PerlInterpreter as _PerlInterpreter
from perlthon._core import hello_from_bin

# Type alias for values returned from Perl
type PerlValue = str | int | float | bool | list[Any] | dict[str, Any] | None

__all__ = [
    "Interpreter",
    "PerlCallable",
    "PerlModule",
    "PerlValue",
    "TypedModule",
    "async_call",
    "async_eval",
    "async_use",
    "call",
    "cpan",
    "eval",
    "generate_stubs",
    "hello",
    "interpreter",
    "register",
    "typed",
    "use",
]

if TYPE_CHECKING:
    from .typed import TypedModule

type InterpreterGetter = Callable[[], _PerlInterpreter]


class _ClosedInterpreterError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Interpreter is closed")


def hello() -> str:
    return hello_from_bin()


_interpreter: _PerlInterpreter | None = None
_interpreter_lock = threading.RLock()
_executor = ThreadPoolExecutor(thread_name_prefix="perlthon")


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

    def __init__(
        self,
        name: str,
        get_interp: InterpreterGetter = _get_interpreter,
        lock: object | None = None,
    ) -> None:
        self._name = name
        self._get_interp = get_interp
        self._lock = lock

    def __repr__(self) -> str:
        return f"PerlModule({self._name!r})"

    def __getattr__(self, name: str) -> PerlCallable:
        return PerlCallable(self._get_interp, self._name, name, self._lock)

    def call(self, method: str, *args: object) -> PerlValue:
        """Call a method on this Perl module (OO-style, passes module as invocant)."""
        if self._lock is None:
            return self._get_interp().call_method(self._name, method, list(args))
        with self._lock:
            return self._get_interp().call_method(self._name, method, list(args))

    async def acall(self, method: str, *args: object) -> PerlValue:
        """Asynchronously call a method on this Perl module."""
        return await _run_async(self.call, method, *args)


class PerlCallable:
    """A lazy reference to a Perl function/method, callable from Python.

    By default, calls the function using its fully qualified name
    (e.g. ``POSIX::floor``). For OO-style method dispatch, use
    ``module.call("method", ...)``.
    """

    def __init__(
        self,
        get_interp: InterpreterGetter,
        module: str,
        method: str,
        lock: object | None = None,
    ) -> None:
        self._get_interp = get_interp
        self._module = module
        self._method = method
        self._lock = lock

    def __repr__(self) -> str:
        return f"PerlCallable({self._module}::{self._method})"

    def __call__(self, *args: object) -> PerlValue:
        fqn = f"{self._module}::{self._method}"
        if self._lock is None:
            return self._get_interp().call_function(fqn, list(args))
        with self._lock:
            return self._get_interp().call_function(fqn, list(args))


class Interpreter:
    """A dedicated Perl interpreter with an explicit lifecycle."""

    def __init__(self) -> None:
        self._interp: _PerlInterpreter | None = _PerlInterpreter()
        self._lock = threading.Lock()

    def _get_interp(self) -> _PerlInterpreter:
        with self._lock:
            if self._interp is None:
                raise _ClosedInterpreterError()
            return self._interp

    def eval(self, code: str) -> PerlValue:
        return self._get_interp().eval(code)

    def use(self, module_name: str) -> PerlModule:
        interp = self._get_interp()
        interp.use_module(module_name)
        return PerlModule(module_name, self._get_interp, self._lock)

    def call(self, function_name: str, *args: object) -> PerlValue:
        return self._get_interp().call_function(function_name, list(args))

    def close(self) -> None:
        with self._lock:
            self._interp = None

    def __enter__(self) -> Interpreter:
        self._get_interp()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


def interpreter() -> Interpreter:
    """Create a dedicated Perl interpreter instance."""
    return Interpreter()


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
        return PerlModule(module_name, _get_interpreter, _interpreter_lock)


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


def register(
    name: str, func: Callable[..., object] | None = None
) -> Callable[..., object]:
    """Register a Python callable as a Perl subroutine."""

    def decorator(callback: Callable[..., object]) -> Callable[..., object]:
        with _interpreter_lock:
            interp = _get_interpreter()
            interp.register_callback(name, callback)
        return callback

    if func is None:
        return decorator
    return decorator(func)


def typed(module_name: str) -> TypedModule:
    from .typed import typed as _typed

    globals()["typed"] = _typed
    return _typed(module_name)


def generate_stubs(modules: list[str], output_dir: str) -> None:
    from .stubs import generate_stubs as _generate_stubs

    _generate_stubs(modules, output_dir)


def __getattr__(name: str) -> object:
    if name == "cpan":
        module = import_module(".cpan", __name__)
        globals()["cpan"] = module
        return module
    if name == "TypedModule":
        from .typed import TypedModule as _TypedModule

        return _TypedModule
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
