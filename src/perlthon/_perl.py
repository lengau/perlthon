from __future__ import annotations

import os
import shutil
from pathlib import Path


def _find_perl() -> str:
    """Find the Perl executable."""
    env_perl = os.environ.get("PERLTHON_PERL")
    if env_perl and shutil.which(env_perl):
        return env_perl

    package_dir = Path(__file__).resolve().parent
    bundled_perl = package_dir / "bin" / "perl"
    if bundled_perl.exists():
        return str(bundled_perl)

    perl = shutil.which("perl")
    if perl is None:
        raise RuntimeError("Perl executable not found")
    return perl
