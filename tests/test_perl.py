"""Tests for the Perl integration API."""

import perlthon


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
