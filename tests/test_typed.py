from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

import perlthon


class TestTypedModule:
    def test_posix_discovers_common_functions(self) -> None:
        posix = perlthon.typed("POSIX")

        functions = posix.available_functions()

        assert "floor" in functions
        assert "ceil" in functions
        assert "pow" in functions

    def test_list_util_discovers_common_functions(self) -> None:
        list_util = perlthon.typed("List::Util")

        functions = list_util.available_functions()

        assert "sum" in functions
        assert "min" in functions
        assert "max" in functions

    def test_available_functions_returns_strings(self) -> None:
        functions = perlthon.typed("POSIX").available_functions()

        assert isinstance(functions, list)
        assert functions
        assert all(isinstance(function, str) for function in functions)

    def test_typed_module_calls_functions(self) -> None:
        posix = perlthon.typed("POSIX")
        list_util = perlthon.typed("List::Util")

        assert posix.floor(3.7) == 3.0
        assert posix.ceil(3.2) == 4.0
        assert posix.pow(2, 3) == 8.0
        assert list_util.sum(1, 2, 3) == 6

    def test_getattr_caches_function_wrappers(self) -> None:
        posix = perlthon.typed("POSIX")

        assert posix.floor is posix.floor

    def test_dir_includes_discovered_functions(self) -> None:
        posix = perlthon.typed("POSIX")

        names = dir(posix)

        assert "floor" in names
        assert "ceil" in names

    def test_collision_safe_aliases_match_stub_resolution(self, monkeypatch) -> None:
        typed_module = importlib.import_module("perlthon.typed")

        monkeypatch.setattr(
            typed_module,
            "_introspect_module",
            lambda module_name: ["sum", "sum_"],
        )
        monkeypatch.setattr(
            typed_module,
            "perl_call",
            lambda target, *args: (target, args),
        )

        module = typed_module.TypedModule("Example")

        assert "sum" in dir(module)
        assert "sum_" in dir(module)
        assert "sum__" in dir(module)
        assert module.sum(1, 2) == ("Example::sum", (1, 2))
        assert module.sum_(1, 2) == ("Example::sum", (1, 2))
        assert module.sum__(3, 4) == ("Example::sum_", (3, 4))

    def test_repr_is_informative(self) -> None:
        posix = perlthon.typed("POSIX")

        representation = repr(posix)

        assert "TypedModule" in representation
        assert "POSIX" in representation

    def test_nonexistent_module_raises(self) -> None:
        with pytest.raises(RuntimeError):
            perlthon.typed("This::Module::Does::Not::Exist")


class TestGenerateStubs:
    def test_docstring_block_escapes_triple_quotes(self) -> None:
        stubs = importlib.import_module("perlthon.stubs")
        block = stubs._docstring_block('Line with """ and trailing "', indent="    ")
        compiled = "def f():\n" + block + "    ...\n"

        assert '\\"\\"\\"' in block
        compile(compiled, "<generated>", "exec")

    def test_module_file_uses_discovered_perl(self, monkeypatch) -> None:
        stubs = importlib.import_module("perlthon.stubs")
        captured = {}

        def fake_find_perl() -> str:
            return "custom-perl"

        class FakeCompletedProcess:
            def __init__(self) -> None:
                self.stdout = ""

        def fake_run(args, **kwargs) -> FakeCompletedProcess:
            del kwargs
            captured["args"] = args
            return FakeCompletedProcess()

        monkeypatch.setattr(stubs, "_find_perl", fake_find_perl)
        monkeypatch.setattr(stubs.subprocess, "run", fake_run)

        assert stubs._module_file("POSIX") is None
        assert captured["args"][0] == "custom-perl"

    def test_module_file_rejects_invalid_module_names(self, monkeypatch) -> None:
        stubs = importlib.import_module("perlthon.stubs")

        def fail_run(*args, **kwargs):
            raise AssertionError("subprocess.run should not be called")

        monkeypatch.setattr(stubs.subprocess, "run", fail_run)

        with pytest.raises(ValueError, match="Invalid Perl module name"):
            stubs._module_file("Foo; system('rm -rf /')")

    def test_importing_perlthon_does_not_eagerly_import_cpan(self) -> None:
        code = (
            "import os, sys\n"
            "before = os.environ.get('PERL5LIB')\n"
            "import perlthon\n"
            "after = os.environ.get('PERL5LIB')\n"
            "assert before == after\n"
            "assert 'perlthon.cpan' not in sys.modules\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            check=False,
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        )

        assert result.returncode == 0, result.stderr

    def test_generate_stubs_creates_pyi_files(self, tmp_path: Path) -> None:
        perlthon.generate_stubs(["POSIX", "List::Util"], output_dir=str(tmp_path))

        assert (tmp_path / "POSIX.pyi").exists()
        assert (tmp_path / "List" / "Util.pyi").exists()

    def test_generated_stub_contains_function_definitions(self, tmp_path: Path) -> None:
        perlthon.generate_stubs(["POSIX", "List::Util"], output_dir=str(tmp_path))

        posix_stub = (tmp_path / "POSIX.pyi").read_text(encoding="utf-8")
        list_util_stub = (tmp_path / "List" / "Util.pyi").read_text(encoding="utf-8")

        assert "class POSIX(TypedModule):" in posix_stub
        assert "def floor(self, *args: Any) -> Any:" in posix_stub
        assert "# Perl: sum -> Python: sum_" in list_util_stub
        assert "def sum_(self, *args: Any) -> Any:" in list_util_stub

    def test_generated_stub_resolves_name_collisions(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        stubs = importlib.import_module("perlthon.stubs")

        monkeypatch.setattr(
            stubs,
            "_introspect_module",
            lambda module_name: ["sum", "sum_"],
        )
        monkeypatch.setattr(stubs, "_pod_docs", lambda module_name, functions: {})

        stubs.generate_stubs(["Example::Collisions"], output_dir=str(tmp_path))

        stub_text = (tmp_path / "Example" / "Collisions.pyi").read_text(
            encoding="utf-8"
        )

        assert "# Perl: sum -> Python: sum_" in stub_text
        assert "# Perl: sum_ -> Python: sum__" in stub_text
        assert "def sum_(self, *args: Any) -> Any:" in stub_text
        assert "def sum__(self, *args: Any) -> Any:" in stub_text
        compile(stub_text, str(tmp_path / "Example" / "Collisions.pyi"), "exec")
