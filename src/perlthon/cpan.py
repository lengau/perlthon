from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

_MODULE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)*$")


def _default_home_lib() -> Path:
    return Path.home() / ".local" / "share" / "perlthon" / "lib"


def get_lib_dir() -> Path:
    """Return the default local::lib root used for CPAN installs."""
    if sys.prefix != sys.base_prefix:
        return Path(sys.prefix) / "perl5lib"
    return _default_home_lib()


def _normalize_lib_dir(lib: str | None) -> Path:
    return Path(lib).expanduser() if lib is not None else get_lib_dir()


def _perl5lib_dir(lib_dir: Path) -> Path:
    return lib_dir / "lib" / "perl5"


def _prepend_env_path(env: dict[str, str], name: str, value: Path) -> None:
    value_str = str(value)
    existing = [entry for entry in env.get(name, "").split(os.pathsep) if entry]
    env[name] = os.pathsep.join(
        [value_str, *[entry for entry in existing if entry != value_str]]
    )


def _apply_local_lib_env(env: dict[str, str], lib_dir: Path) -> None:
    lib_dir = lib_dir.expanduser()
    _prepend_env_path(env, "PATH", lib_dir / "bin")
    _prepend_env_path(env, "PERL5LIB", _perl5lib_dir(lib_dir))
    existing_roots = [
        entry for entry in env.get("PERL_LOCAL_LIB_ROOT", "").split(os.pathsep) if entry
    ]
    lib_root = str(lib_dir)
    env["PERL_LOCAL_LIB_ROOT"] = os.pathsep.join(
        [lib_root, *[entry for entry in existing_roots if entry != lib_root]]
    )
    env["PERL_MB_OPT"] = f"--install_base {shlex.quote(str(lib_dir))}"
    env["PERL_MM_OPT"] = f"INSTALL_BASE={shlex.quote(str(lib_dir))}"


def _perl_env(lib_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    _apply_local_lib_env(env, lib_dir)
    return env


def _find_perl() -> str:
    configured = os.environ.get("PERLTHON_PERL")
    if configured:
        return configured

    package_dir = Path(__file__).resolve().parent
    bundled_perl = package_dir / "bin" / "perl"
    if bundled_perl.exists():
        return str(bundled_perl)

    perl = shutil.which("perl")
    if perl is None:
        raise RuntimeError("Perl executable not found")
    return perl


def _validate_modules(modules: tuple[str, ...]) -> None:
    invalid = [module for module in modules if not _MODULE_NAME_RE.fullmatch(module)]
    if invalid:
        joined = ", ".join(sorted(invalid))
        raise ValueError(f"invalid Perl module name(s): {joined}")


def _reset_interpreter() -> None:
    import perlthon

    perlthon._interpreter = None


def install(*modules: str, lib: str | None = None) -> None:
    """Install one or more Perl modules with cpanm."""
    if not modules:
        return

    _validate_modules(modules)

    cpanm = shutil.which("cpanm")
    if cpanm is None:
        raise RuntimeError(
            "cpanm (App::cpanminus) is required to install Perl modules. "
            "Install it first, for example with `apt-get install cpanminus`."
        )

    lib_dir = _normalize_lib_dir(lib)
    lib_dir.mkdir(parents=True, exist_ok=True)
    env = _perl_env(lib_dir)
    result = subprocess.run(
        [_find_perl(), cpanm, "-L", str(lib_dir), *modules],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )
    if result.returncode != 0:
        output = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"cpanm failed to install {', '.join(modules)}: {output}")

    _apply_local_lib_env(os.environ, lib_dir)
    _reset_interpreter()


def is_installed(module: str) -> bool:
    """Return True when a Perl module can be required successfully."""
    if not _MODULE_NAME_RE.fullmatch(module):
        return False

    result = subprocess.run(
        [_find_perl(), "-e", f"print(eval {{ require {module}; 1 }} ? 1 : 0)"],
        capture_output=True,
        check=False,
        env=_perl_env(get_lib_dir()),
        text=True,
    )
    if result.returncode != 0:
        return False
    return result.stdout.strip() == "1"


def installed() -> list[str]:
    """List accessible non-core Perl modules."""
    lib_dir = get_lib_dir()
    env = _perl_env(lib_dir)
    script = "\n".join(
        [
            "use strict;",
            "use warnings;",
            "use Config qw(%Config);",
            "use ExtUtils::Installed;",
            "use Module::CoreList;",
            (
                "my @extra_libs = grep { length } split /\\Q$Config{path_sep}\\E/, "
                "($ENV{PERL5LIB} // q{});"
            ),
            "my $installed = ExtUtils::Installed->new(extra_libs => \\@extra_libs);",
            "my %modules;",
            "for my $module ($installed->modules()) {",
            "    next if $module eq q{perl};",
            "    next if Module::CoreList::is_core($module);",
            "    $modules{$module} = 1;",
            "}",
            "print join qq{\\n}, sort keys %modules;",
        ]
    )
    result = subprocess.run(
        [_find_perl(), "-e", script],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )
    if result.returncode != 0:
        output = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"failed to list installed Perl modules: {output}")

    stdout = result.stdout.strip()
    return stdout.splitlines() if stdout else []


__all__ = ["get_lib_dir", "install", "installed", "is_installed"]
