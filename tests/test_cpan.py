from __future__ import annotations

import shutil
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
