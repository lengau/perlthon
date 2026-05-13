from __future__ import annotations

import re

_PERL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(::[A-Za-z_][A-Za-z0-9_]*)*$")


def _validate_perl_name(name: str, *, kind: str) -> str:
    if not _PERL_NAME_RE.fullmatch(name):
        raise ValueError(f"Invalid Perl {kind} name: {name!r}")
    return name


def validate_module_name(name: str) -> str:
    return _validate_perl_name(name, kind="module")


def validate_function_name(name: str) -> str:
    return _validate_perl_name(name, kind="function")
