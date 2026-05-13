from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from perlthon import cpan


def test_is_installed_returns_true_for_core_modules() -> None:
    assert cpan.is_installed("POSIX") is True
    assert cpan.is_installed("List::Util") is True


def test_is_installed_returns_false_for_missing_module() -> None:
    assert cpan.is_installed("Perlthon::Definitely::Missing::Module") is False


def test_get_lib_dir_returns_path() -> None:
    assert isinstance(cpan.get_lib_dir(), Path)


def test_installed_returns_list() -> None:
    assert isinstance(cpan.installed(), list)


def test_importing_perlthon_does_not_mutate_environment() -> None:
    pythonpath = os.pathsep.join(
        entry
        for entry in [str(Path.cwd() / "src"), os.environ.get("PYTHONPATH", "")]
        if entry
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import json
                import os

                before = dict(os.environ)
                import perlthon  # noqa: F401
                after = dict(os.environ)
                changed = {
                    key: [before.get(key), after.get(key)]
                    for key in sorted(set(before) | set(after))
                    if before.get(key) != after.get(key)
                }
                print(json.dumps(changed, sort_keys=True))
                """
            ),
        ],
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONPATH": pythonpath},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "{}"


def test_importing_cpan_does_not_require_home_directory() -> None:
    pythonpath = os.pathsep.join(
        entry
        for entry in [str(Path.cwd() / "src"), os.environ.get("PYTHONPATH", "")]
        if entry
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import pathlib

                def fail_home(cls):
                    raise RuntimeError("home used at import time")

                pathlib.Path.home = classmethod(fail_home)
                import perlthon
                from perlthon import cpan  # noqa: F401
                """
            ),
        ],
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONPATH": pythonpath},
        text=True,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("module_name", ["Bad Module", "Foo-Bar", "", "::Broken"])
def test_install_raises_for_invalid_module_names(module_name: str) -> None:
    with pytest.raises(ValueError, match="invalid Perl module"):
        cpan.install(module_name)


def test_install_raises_helpful_error_when_cpanm_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_which = shutil.which

    def fake_which(name: str) -> str | None:
        if name == "cpanm":
            return None
        return real_which(name)

    monkeypatch.setattr(shutil, "which", fake_which)

    with pytest.raises(RuntimeError, match="cpanm"):
        cpan.install("Text::CSV")


def test_apply_local_lib_env_quotes_paths_with_spaces() -> None:
    env: dict[str, str] = {}
    lib_dir = Path.cwd() / "dir with spaces" / "perl5"

    cpan._apply_local_lib_env(env, lib_dir)

    assert env["PERL_MB_OPT"] == f"--install_base '{lib_dir}'"
    assert env["PERL_MM_OPT"] == f"INSTALL_BASE='{lib_dir}'"


@pytest.mark.slow
def test_install_installs_module_into_custom_lib() -> None:
    lib_dir = Path.cwd() / ".pytest-perl5lib"
    if lib_dir.exists():
        shutil.rmtree(lib_dir)

    try:
        cpan.install("Try::Tiny", lib=str(lib_dir))
        assert cpan.is_installed("Try::Tiny") is True
        assert "Try::Tiny" in cpan.installed()
    finally:
        if lib_dir.exists():
            shutil.rmtree(lib_dir)
