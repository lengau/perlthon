from __future__ import annotations

from typing import Any

from . import (
    PerlValue,
)
from . import (
    call as perl_call,
)
from . import (
    eval as perl_eval,
)
from . import (
    use as perl_use,
)

_EXCLUDED_SYMBOLS = frozenset(
    {
        "AUTOLOAD",
        "BEGIN",
        "DESTROY",
        "END",
        "EXPORT",
        "EXPORT_OK",
        "EXPORT_TAGS",
        "ISA",
        "VERSION",
        "bootstrap",
        "import",
        "unimport",
    }
)


def _perl_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _is_discoverable_symbol(name: str) -> bool:
    if not name or name in _EXCLUDED_SYMBOLS or name.startswith("_"):
        return False
    if "::" in name or name.endswith("::"):
        return False
    return not all(char.isupper() or char.isdigit() or char == "_" for char in name)


def _introspect_module(module_name: str) -> list[str]:
    perl_use(module_name)
    result = perl_eval(
        f"""
        do {{
            my $module = {_perl_quote(module_name)};
            no strict 'refs';
            my @functions = (
                @{{"${{module}}::EXPORT"}},
                @{{"${{module}}::EXPORT_OK"}},
            );
            for my $name (keys %{{"${{module}}::"}}) {{
                next unless defined &{{"${{module}}::${{name}}"}};
                push @functions, $name;
            }}
            my %seen;
            [ sort grep {{ !$seen{{$_}}++ }} @functions ];
        }}
        """
    )
    if not isinstance(result, list):
        return []
    return sorted(
        {
            name
            for name in result
            if isinstance(name, str) and _is_discoverable_symbol(name)
        }
    )


class TypedModule:
    def __init__(self, module_name: str) -> None:
        self._module_name = module_name
        self._functions = _introspect_module(module_name)

    def __repr__(self) -> str:
        count = len(self._functions)
        return f"TypedModule(module={self._module_name!r}, functions={count})"

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | set(self._functions))

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._functions:
            msg = f"Module {self._module_name} has no function {name!r}"
            raise AttributeError(msg)

        def caller(*args: object) -> PerlValue:
            return perl_call(f"{self._module_name}::{name}", *args)

        caller.__name__ = name
        caller.__qualname__ = f"{self._module_name}.{name}"
        self.__dict__[name] = caller
        return caller

    def available_functions(self) -> list[str]:
        return list(self._functions)


def typed(module_name: str) -> TypedModule:
    return TypedModule(module_name)
