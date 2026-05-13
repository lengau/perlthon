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

    def test_render_stub_renames_keyword_functions(self) -> None:
        stubs = importlib.import_module("perlthon.stubs")
        # "assert" is a Python keyword; it must be renamed to "assert_"
        result = stubs._render_stub("Foo::Bar", ["assert", "raise", "normal_func"])

        assert "def assert_(self" in result, "keyword 'assert' should be renamed to 'assert_'"
        assert "def raise_(self" in result, "keyword 'raise' should be renamed to 'raise_'"
        assert "def normal_func(self" in result, "non-keyword name should be unchanged"
        # Make sure the raw keyword does NOT appear as a method definition
        assert "def assert(self" not in result
        assert "def raise(self" not in result
        # The resulting stub text must be valid Python
        compile(result, "<generated>", "exec")

    def test_generated_stub_contains_function_definitions(self, tmp_path: Path) -> None:
        perlthon.generate_stubs(["POSIX", "List::Util"], output_dir=str(tmp_path))

        posix_stub = (tmp_path / "POSIX.pyi").read_text(encoding="utf-8")
        list_util_stub = (tmp_path / "List" / "Util.pyi").read_text(encoding="utf-8")

        assert "class POSIX(TypedModule):" in posix_stub
        assert "def floor(self, *args: Any) -> Any:" in posix_stub
        assert "def sum(self, *args: Any) -> Any:" in list_util_stub


class TestKeywordRenaming:
    """TypedModule must reverse keyword-renamed attributes to dispatch correctly."""

    def test_keyword_function_accessible_with_suffix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A Perl function named after a Python keyword (e.g. 'not') should be
        accessible as 'not_' on the TypedModule instance."""
        import perlthon.typed as typed_mod
        from unittest.mock import MagicMock, patch

        # Patch _introspect_module to simulate a module exporting 'not'
        with patch.object(typed_mod, "_introspect_module", return_value={"not": None}):
            mod = typed_mod.TypedModule("FakeModule")
            # 'not_' should be in dir()
            assert "not_" in dir(mod)
            assert "not" not in dir(mod)

    def test_keyword_function_dispatches_to_perl_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Calling mod.not_() must dispatch to Perl 'FakeModule::not', not 'FakeModule::not_'."""
        import perlthon.typed as typed_mod
        from unittest.mock import patch, call as mock_call

        captured = []

        def fake_perl_call(name: str, *args: object) -> str:
            captured.append(name)
            return "ok"

        with patch.object(typed_mod, "_introspect_module", return_value={"not": None}), \
             patch.object(typed_mod, "perl_call", fake_perl_call):
            mod = typed_mod.TypedModule("FakeModule")
            mod.not_()  # should call FakeModule::not, not FakeModule::not_

        assert captured == ["FakeModule::not"]

    def test_ambiguous_exports_raise_at_init(self) -> None:
        """If a Perl module exports both 'assert' and 'assert_', TypedModule must raise."""
        import perlthon.typed as typed_mod
        from unittest.mock import patch

        with patch.object(typed_mod, "_introspect_module", return_value={"assert": None, "assert_": None}):
            with pytest.raises(ValueError, match="Ambiguous Perl exports"):
                typed_mod.TypedModule("BadModule")
