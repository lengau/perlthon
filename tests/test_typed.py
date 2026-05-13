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

    def test_safe_aliases_allow_keyword_named_functions(self, monkeypatch) -> None:
        typed_module = importlib.import_module("perlthon.typed")

        monkeypatch.setattr(
            typed_module,
            "_introspect_module",
            lambda module_name: ["class", "print"],
        )
        monkeypatch.setattr(
            typed_module,
            "perl_call",
            lambda target, *args: (target, args),
        )

        module = typed_module.TypedModule("Example")

        assert "class_" in dir(module)
        assert "print" in dir(module)
        assert "print_" not in dir(module)
        assert module.class_(1) == ("Example::class", (1,))
        assert module.print("value") == ("Example::print", ("value",))
        assert getattr(module, "class") is module.class_

    def test_keyword_alias_caches_callable_when_alias_accessed_first(
        self, monkeypatch
    ) -> None:
        typed_module = importlib.import_module("perlthon.typed")

        monkeypatch.setattr(
            typed_module,
            "_introspect_module",
            lambda module_name: ["class"],
        )
        monkeypatch.setattr(
            typed_module,
            "perl_call",
            lambda target, *args: (target, args),
        )

        module = typed_module.TypedModule("Example")

        alias_first = module.class_
        alias_name = "class_"

        assert alias_first is getattr(module, "class")
        assert module.class_ is getattr(module, alias_name)

    def test_keyword_alias_caches_callable_when_original_accessed_first(
        self, monkeypatch
    ) -> None:
        typed_module = importlib.import_module("perlthon.typed")

        monkeypatch.setattr(
            typed_module,
            "_introspect_module",
            lambda module_name: ["class"],
        )
        monkeypatch.setattr(
            typed_module,
            "perl_call",
            lambda target, *args: (target, args),
        )

        module = typed_module.TypedModule("Example")

        original_first = getattr(module, "class")
        alias_name = "class_"

        assert original_first is module.class_
        assert module.class_ is getattr(module, alias_name)

    def test_build_name_map_preserves_builtin_names(self) -> None:
        typed_module = importlib.import_module("perlthon.typed")

        assert typed_module.build_name_map(["sum_", "sum"]) == {
            "sum": "sum",
            "sum_": "sum_",
        }

    def test_build_name_map_preserves_real_name_over_keyword_alias(self) -> None:
        typed_module = importlib.import_module("perlthon.typed")

        assert typed_module.build_name_map(["class", "class_"]) == {
            "class_": "class_",
            "class__": "class",
        }

    def test_builtin_names_remain_directly_addressable(self, monkeypatch) -> None:
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
        assert "sum__" not in dir(module)
        assert module.sum(1, 2) == ("Example::sum", (1, 2))
        assert module.sum_(3, 4) == ("Example::sum_", (3, 4))

    def test_reserved_methods_are_not_overwritten_by_alias_caching(
        self, monkeypatch
    ) -> None:
        typed_module = importlib.import_module("perlthon.typed")

        monkeypatch.setattr(
            typed_module,
            "_introspect_module",
            lambda module_name: ["available_functions"],
        )
        monkeypatch.setattr(
            typed_module,
            "perl_call",
            lambda target, *args: (target, args),
        )

        module = typed_module.TypedModule("Example")

        assert module.available_functions_() == ("Example::available_functions", ())
        assert module.available_functions() == ["available_functions"]
        assert "available_functions" not in module.__dict__

    def test_keyword_alias_yields_to_existing_function_name(
        self, monkeypatch
    ) -> None:
        typed_module = importlib.import_module("perlthon.typed")

        monkeypatch.setattr(
            typed_module,
            "_introspect_module",
            lambda module_name: ["class", "class_"],
        )
        monkeypatch.setattr(
            typed_module,
            "perl_call",
            lambda target, *args: (target, args),
        )

        module = typed_module.TypedModule("Example")

        assert module.class_(1) == ("Example::class_", (1,))
        assert getattr(module, "class")(2) == ("Example::class", (2,))
        assert module.class__(3) == ("Example::class", (3,))
        assert getattr(module, "class") is module.class__

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
        assert "def sum(self, *args: Any) -> Any:" in list_util_stub
        assert "# Perl: sum -> Python: sum_" not in list_util_stub

    def test_generated_stub_renames_only_python_keywords(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        stubs = importlib.import_module("perlthon.stubs")

        monkeypatch.setattr(
            stubs,
            "_introspect_module",
            lambda module_name: ["class", "print", "normal"],
        )
        monkeypatch.setattr(stubs, "_pod_docs", lambda module_name, functions: {})

        stubs.generate_stubs(["Example::Keywords"], output_dir=str(tmp_path))

        stub_text = (tmp_path / "Example" / "Keywords.pyi").read_text(encoding="utf-8")

        assert "# Perl: class -> Python: class_" in stub_text
        assert "# Perl: print -> Python: print_" not in stub_text
        assert "def class_(self, *args: Any) -> Any:" in stub_text
        assert "def print(self, *args: Any) -> Any:" in stub_text
        assert "def normal(self, *args: Any) -> Any:" in stub_text
        compile(stub_text, str(tmp_path / "Example" / "Keywords.pyi"), "exec")

    def test_generated_stub_resolves_name_collisions(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        stubs = importlib.import_module("perlthon.stubs")

        monkeypatch.setattr(
            stubs,
            "_introspect_module",
            lambda module_name: ["sum_", "sum"],
        )
        monkeypatch.setattr(stubs, "_pod_docs", lambda module_name, functions: {})

        stubs.generate_stubs(["Example::Collisions"], output_dir=str(tmp_path))

        stub_text = (tmp_path / "Example" / "Collisions.pyi").read_text(
            encoding="utf-8"
        )

        assert "# Perl: sum -> Python: sum_" not in stub_text
        assert "# Perl: sum_ -> Python: sum__" not in stub_text
        assert "def sum(self, *args: Any) -> Any:" in stub_text
        assert "def sum_(self, *args: Any) -> Any:" in stub_text
        compile(stub_text, str(tmp_path / "Example" / "Collisions.pyi"), "exec")

    def test_generated_stub_preserves_real_name_over_keyword_alias(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        stubs = importlib.import_module("perlthon.stubs")

        monkeypatch.setattr(
            stubs,
            "_introspect_module",
            lambda module_name: ["class", "class_"],
        )
        monkeypatch.setattr(stubs, "_pod_docs", lambda module_name, functions: {})

        stubs.generate_stubs(["Example::Keywords"], output_dir=str(tmp_path))

        stub_text = (tmp_path / "Example" / "Keywords.pyi").read_text(encoding="utf-8")

        assert "# Perl: class -> Python: class__" in stub_text
        assert "# Perl: class_ -> Python: class__" not in stub_text
        assert "def class_(self, *args: Any) -> Any:" in stub_text
        assert "def class__(self, *args: Any) -> Any:" in stub_text
        compile(stub_text, str(tmp_path / "Example" / "Keywords.pyi"), "exec")

    def test_generated_posix_stub_is_valid_python(self, tmp_path: Path) -> None:
        perlthon.generate_stubs(["POSIX"], output_dir=str(tmp_path))

        posix_stub = (tmp_path / "POSIX.pyi").read_text(encoding="utf-8")

        compile(posix_stub, str(tmp_path / "POSIX.pyi"), "exec")
