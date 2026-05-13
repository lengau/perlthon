"""Tests for the Perl integration API."""

import pytest

import perlthon
from perlthon._core import PerlInterpreter


class TestEval:
    def test_eval_arithmetic(self):
        result = perlthon.eval("2 + 2")
        assert result == 4

    def test_eval_string(self):
        result = perlthon.eval('"hello " . "world"')
        assert result == "hello world"

    def test_eval_undef(self):
        result = perlthon.eval("undef")
        assert result is None

    def test_eval_array_ref(self):
        result = perlthon.eval("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_eval_hash_ref(self):
        result = perlthon.eval('{"key" => "value"}')
        assert result == {"key": "value"}


class TestUse:
    def test_use_returns_perl_module(self):
        mod = perlthon.use("POSIX")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_invalid_module_raises(self):
        import pytest

        with pytest.raises(RuntimeError):
            perlthon.use("This::Module::Does::Not::Exist")


class TestCall:
    def test_call_posix_floor(self):
        perlthon.use("POSIX")
        result = perlthon.call("POSIX::floor", 3.7)
        assert result == 3.0

    def test_call_posix_ceil(self):
        perlthon.use("POSIX")
        result = perlthon.call("POSIX::ceil", 3.2)
        assert result == 4.0


class TestPerlModule:
    def test_module_method_call(self):
        posix = perlthon.use("POSIX")
        result = posix.floor(3.7)
        assert result == 3.0

    def test_module_repr(self):
        posix = perlthon.use("POSIX")
        assert "POSIX" in repr(posix)


class TestNameValidation:
    @pytest.mark.parametrize(
        "module_name",
        [
            "Bad Module",
            "Foo; system('echo injected')",
            "strict'; print qq(INJECTED\\n); 1; }; #",
        ],
    )
    def test_use_validates_module_names(self, module_name: str) -> None:
        with pytest.raises(ValueError, match="Invalid Perl module name"):
            perlthon.use(module_name)

    @pytest.mark.parametrize(
        "function_name",
        [
            "POSIX::floor; system('echo injected')",
            "POSIX::floor # comment",
            "POSIX::floor\nprint qq(INJECTED)",
        ],
    )
    def test_call_validates_function_names(self, function_name: str) -> None:
        with pytest.raises(ValueError, match="Invalid Perl function name"):
            perlthon.call(function_name, 3.7)

    def test_module_proxy_validates_method_names(self) -> None:
        posix = perlthon.use("POSIX")

        with pytest.raises(ValueError, match="Invalid Perl function name"):
            posix.call("floor; print qq(INJECTED)", 3.7)

    def test_module_attribute_validates_method_names(self) -> None:
        posix = perlthon.use("POSIX")

        with pytest.raises(ValueError, match="Invalid Perl function name"):
            getattr(posix, "floor; print qq(INJECTED)")

    def test_interpreter_validates_names(self) -> None:
        interp = perlthon.interpreter()

        with pytest.raises(ValueError, match="Invalid Perl module name"):
            interp.use("Bad Module")
        with pytest.raises(ValueError, match="Invalid Perl function name"):
            interp.call("POSIX::floor; print qq(INJECTED)", 3.7)

    def test_core_interpreter_validates_names(self) -> None:
        interp = PerlInterpreter()

        with pytest.raises(ValueError, match="Invalid Perl module name"):
            interp.use_module("Bad Module")
        with pytest.raises(ValueError, match="Invalid Perl function name"):
            interp.call_function("POSIX::floor; print qq(INJECTED)", [3.7])
        with pytest.raises(ValueError, match="Invalid Perl function name"):
            interp.call_method("POSIX", "floor; print qq(INJECTED)", [3.7])
