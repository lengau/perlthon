"""Perlthon: Import and run Perl modules from Python."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from perlthon._core import PerlInterpreter as _PerlInterpreter
from perlthon._core import hello_from_bin

# Type alias for values returned from Perl
type PerlValue = str | int | float | bool | list[Any] | dict[str, Any] | None

if TYPE_CHECKING:
    from .typed import TypedModule


def hello() -> str:
    return hello_from_bin()


_interpreter: _PerlInterpreter | None = None


def _get_interpreter() -> _PerlInterpreter:
    global _interpreter
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
        return self._interp.call_method(self._name, method, list(args))


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
        return self._interp.call_function(fqn, list(args))


def use(module_name: str) -> PerlModule:
    """Load a Perl module (equivalent to Perl's ``use Module``).

    Args:
        module_name: Fully qualified Perl module name (e.g. ``"Text::CSV"``).

    Returns:
        A :class:`PerlModule` proxy that supports method calls.
    """
    interp = _get_interpreter()
    interp.use_module(module_name)
    return PerlModule(module_name)


def call(function_name: str, *args: object) -> PerlValue:
    """Call a Perl function by its fully qualified name.

    Args:
        function_name: E.g. ``"POSIX::floor"``.
        *args: Arguments to pass to the Perl function.

    Returns:
        The return value from Perl, converted to a Python type.
    """
    interp = _get_interpreter()
    return interp.call_function(function_name, list(args))


def eval(code: str) -> PerlValue:
    """Evaluate a string of Perl code and return the result.

    Args:
        code: Perl source code to evaluate.

    Returns:
        The result of the evaluation, converted to a Python type.
    """
    interp = _get_interpreter()
    return interp.eval(code)


def typed(module_name: str) -> TypedModule:
    from .typed import typed as _typed

    globals()["typed"] = _typed
    return _typed(module_name)


def generate_stubs(modules: list[str], output_dir: str) -> None:
    from .stubs import generate_stubs as _generate_stubs

    _generate_stubs(modules, output_dir)


def __getattr__(name: str) -> object:
    if name == "TypedModule":
        from .typed import TypedModule as _TypedModule

        return _TypedModule
    if name == "cpan":
        module = importlib.import_module(".cpan", __name__)
        globals()[name] = module
        return module
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
