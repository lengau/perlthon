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


def test_importing_cpan_does_not_mutate_environment() -> None:
    code = "\n".join(
        [
            "import os",
            "import sys",
            "import types",
            "from pathlib import Path",
            "repo = Path.cwd()",
            "sys.path.insert(0, str(repo / 'src'))",
            "core = types.ModuleType('perlthon._core')",
            "core.PerlInterpreter = type('PerlInterpreter', (), {})",
            "core.hello_from_bin = lambda: 'hello'",
            "sys.modules['perlthon._core'] = core",
            "before = dict(os.environ)",
            "from perlthon import cpan",
            "after = dict(os.environ)",
            (
                "diff = {k: (before.get(k), after.get(k)) "
                "for k in set(before) | set(after) "
                "if before.get(k) != after.get(k)}"
            ),
            "assert not diff, f'Environment mutated on import: {diff}'",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 0, result.stderr


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


def test_install_uses_trusted_https_mirror_and_sanitizes_cpanm_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cpan._cpanm_supports_verify.cache_clear()
    calls: list[tuple[list[str], dict[str, str] | None]] = []
    monkeypatch.setattr(
        shutil, "which", lambda name: "/fake/cpanm" if name == "cpanm" else None
    )
    monkeypatch.setattr(cpan, "_find_perl", lambda: "/usr/bin/perl")
    monkeypatch.setattr(cpan, "_reset_interpreter", lambda: None)
    monkeypatch.setenv("PERL_CPANM_OPT", "--from http://evil.invalid")
    monkeypatch.setenv("PERL_CPANM_HOME", "/unsafe/home")

    def fake_run(
        args: list[str],
        capture_output: bool,
        check: bool,
        env: dict[str, str] | None = None,
        text: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        calls.append((args, env))
        if args == ["/usr/bin/perl", "/fake/cpanm", "--help"]:
            return subprocess.CompletedProcess(args, 0, stdout="cpanm help", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    cpan.install("Try::Tiny")

    install_args, install_env = calls[-1]
    assert install_args == [
        "/usr/bin/perl",
        "/fake/cpanm",
        "--from",
        "https://cpan.metacpan.org",
        "--mirror-only",
        "-L",
        str(cpan.get_lib_dir()),
        "Try::Tiny",
    ]
    assert install_env is not None
    assert "PERL_CPANM_OPT" not in install_env
    assert "PERL_CPANM_HOME" not in install_env


def test_install_accepts_https_mirror_override(monkeypatch: pytest.MonkeyPatch) -> None:
    cpan._cpanm_supports_verify.cache_clear()
    commands: list[list[str]] = []
    monkeypatch.setattr(
        shutil, "which", lambda name: "/fake/cpanm" if name == "cpanm" else None
    )
    monkeypatch.setattr(cpan, "_find_perl", lambda: "/usr/bin/perl")
    monkeypatch.setattr(cpan, "_reset_interpreter", lambda: None)

    def fake_run(
        args: list[str],
        capture_output: bool,
        check: bool,
        env: dict[str, str] | None = None,
        text: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        return subprocess.CompletedProcess(
            args, 0, stdout="--verify available", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    cpan.install("Try::Tiny", mirror="https://cpan.example.test/root")

    assert commands[-1] == [
        "/usr/bin/perl",
        "/fake/cpanm",
        "--from",
        "https://cpan.example.test/root",
        "--mirror-only",
        "--verify",
        "-L",
        str(cpan.get_lib_dir()),
        "Try::Tiny",
    ]


@pytest.mark.parametrize("mirror", ["http://cpan.example.test", "cpan.example.test"])
def test_install_rejects_insecure_mirror(
    monkeypatch: pytest.MonkeyPatch, mirror: str
) -> None:
    monkeypatch.setattr(
        shutil, "which", lambda name: "/fake/cpanm" if name == "cpanm" else None
    )

    with pytest.raises(ValueError, match="HTTPS URL"):
        cpan.install("Try::Tiny", mirror=mirror)


@pytest.mark.parametrize(
    "mirror",
    [
        "https://user@cpan.example.test/root",
        "https://user:pass@cpan.example.test/root",
    ],
)
def test_normalize_mirror_rejects_credentials(mirror: str) -> None:
    repo = Path(__file__).resolve().parents[1]
    pythonpath = os.pathsep.join(
        entry
        for entry in [str(repo / "src"), os.environ.get("PYTHONPATH", "")]
        if entry
    )
    code = textwrap.dedent(
        f"""
        import sys
        import types

        core = types.ModuleType("perlthon._core")
        core.PerlInterpreter = type("PerlInterpreter", (), {{}})
        core.hello_from_bin = lambda: "hello"
        sys.modules["perlthon._core"] = core

        from perlthon import cpan

        try:
            cpan._normalize_mirror({mirror!r})
        except ValueError as exc:
            assert str(exc) == (
                "Mirror URLs must not contain credentials; "
                "use external auth mechanisms instead."
            )
        else:
            raise AssertionError("expected ValueError")
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        check=False,
        cwd=repo,
        env={**os.environ, "PYTHONPATH": pythonpath},
        text=True,
    )

    assert result.returncode == 0, result.stderr


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
