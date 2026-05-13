from __future__ import annotations

import builtins
import keyword
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

_PYTHON_RESERVED_NAMES = frozenset(
    name for name in dir(builtins) if name.isidentifier() and not name.startswith("_")
)

_RESERVED_TYPED_METHOD_NAMES = frozenset({"available_functions"})


def _perl_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _is_discoverable_symbol(name: str) -> bool:
    if not name or name in _EXCLUDED_SYMBOLS or name.startswith("_"):
        return False
    if "::" in name or name.endswith("::"):
        return False
    return not all(char.isupper() or char.isdigit() or char == "_" for char in name)


def _needs_python_safe_name(name: str) -> bool:
    return (
        keyword.iskeyword(name)
        or keyword.issoftkeyword(name)
        or name in _PYTHON_RESERVED_NAMES
    )


def _python_safe_name(name: str) -> str:
    return f"{name}_" if _needs_python_safe_name(name) else name


def _python_name_map(functions: list[str]) -> dict[str, str]:
    used_names = set(_RESERVED_TYPED_METHOD_NAMES)
    name_map: dict[str, str] = {}
    for function_name in functions:
        if not function_name.isidentifier():
            continue
        python_name = _python_safe_name(function_name)
        while python_name in used_names:
            python_name += "_"
        used_names.add(python_name)
        name_map[python_name] = function_name
    return name_map


def _resolve_function_name(
    name: str, name_map: dict[str, str], functions: set[str]
) -> str | None:
    if resolved_name := name_map.get(name):
        return resolved_name
    if name in functions:
        return name
    return None


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
        self._function_set = set(self._functions)
        self._name_map = _python_name_map(self._functions)

    def __repr__(self) -> str:
        count = len(self._functions)
        return f"TypedModule(module={self._module_name!r}, functions={count})"

    def __dir__(self) -> list[str]:
        return sorted(set(super().__dir__()) | self._function_set | set(self._name_map))

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        resolved_name = _resolve_function_name(name, self._name_map, self._function_set)
        if resolved_name is None:
            msg = f"Module {self._module_name} has no function {name!r}"
            raise AttributeError(msg)

        def caller(*args: object) -> PerlValue:
            return perl_call(f"{self._module_name}::{resolved_name}", *args)

        caller.__name__ = name
        caller.__qualname__ = f"{self._module_name}.{name}"
        self.__dict__[name] = caller
        if (
            resolved_name != name
            and self._name_map.get(resolved_name, resolved_name) == resolved_name
        ):
            self.__dict__.setdefault(resolved_name, caller)
        return caller

    def available_functions(self) -> list[str]:
        return list(self._functions)


def typed(module_name: str) -> TypedModule:
    return TypedModule(module_name)
