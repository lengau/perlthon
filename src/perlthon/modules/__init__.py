"""Import Perl modules using Python's attribute syntax.

Mapping rules:
- ``::`` in Perl becomes ``.`` in Python (attribute access)
- ``__`` (double underscore) in Python becomes ``.`` in Perl (for rare dotted names)

Examples::

    from perlthon.modules import POSIX
    POSIX.floor(3.7)  # calls POSIX::floor(3.7)

    from perlthon.modules import File
    File.Basename.basename('/usr/bin/perl')  # calls File::Basename::basename(...)

    from perlthon import modules
    modules.List.Util.sum(1, 2, 3)  # calls List::Util::sum(1, 2, 3)
"""

from __future__ import annotations

from typing import Any

import perlthon


class _PerlNamespace:
    """Lazy proxy that accumulates Perl namespace segments.

    The last segment accessed before a call is treated as the function name.
    All preceding segments form the module name (joined with ``::``).
    """

    def __init__(self, parts: list[str] | None = None) -> None:
        object.__setattr__(self, "_parts", parts or [])

    def __getattr__(self, name: str) -> _PerlNamespace:
        if name.startswith("_"):
            raise AttributeError(name)
        # Double underscore maps to dot in Perl (for rare dotted names)
        perl_segment = name.replace("__", ".")
        return _PerlNamespace([*self._parts, perl_segment])

    def __call__(self, *args: Any) -> Any:
        """Call the Perl function.

        Everything except the last segment is the module name,
        the last segment is the function name.
        """
        parts = self._parts
        if not parts:
            msg = "Cannot call empty namespace"
            raise TypeError(msg)

        if len(parts) == 1:
            # Single segment: treat as a function in main::
            module_name = "main"
            func_name = parts[0]
        else:
            module_name = "::".join(parts[:-1])
            func_name = parts[-1]

        perlthon.use(module_name)
        return perlthon.call(f"{module_name}::{func_name}", *args)

    def __repr__(self) -> str:
        return f"PerlNamespace({'::'.join(self._parts)})"


def __getattr__(name: str) -> _PerlNamespace:
    """Module-level attribute access creates a namespace proxy."""
    if name.startswith("_"):
        raise AttributeError(name)
    # Double underscore maps to dot in Perl (for rare dotted names)
    perl_segment = name.replace("__", ".")
    return _PerlNamespace([perl_segment])
