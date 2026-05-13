"""Tests for dedicated Perl interpreter instances."""

import pytest

import perlthon


class TestInterpreterContextManager:
    def test_context_manager_usage(self):
        with perlthon.interpreter() as perl:
            perl.eval("$main::context_value = 42")

            assert perl.eval("$main::context_value") == 42

            posix = perl.use("POSIX")
            assert posix.floor(3.7) == 3.0
            assert perl.call("POSIX::ceil", 3.2) == 4.0

    def test_explicit_close(self):
        interp = perlthon.Interpreter()
        interp.eval("$main::close_value = 7")
        assert interp.eval("$main::close_value") == 7

        interp.close()

        with pytest.raises(RuntimeError, match="closed"):
            interp.eval("1 + 1")

    def test_state_isolated_between_interpreters(self):
        interp_one = perlthon.Interpreter()
        interp_two = perlthon.Interpreter()

        try:
            interp_one.eval('$main::shared_value = "first"')
            interp_two.eval('$main::shared_value = "second"')

            assert interp_one.eval("$main::shared_value") == "first"
            assert interp_two.eval("$main::shared_value") == "second"
        finally:
            interp_one.close()
            interp_two.close()

    def test_global_functions_remain_available(self):
        assert perlthon.eval("40 + 2") == 42

        posix = perlthon.use("POSIX")
        assert posix.floor(8.9) == 8.0
        assert perlthon.call("POSIX::ceil", 8.1) == 9.0

    def test_use_after_close_raises(self):
        interp = perlthon.Interpreter()
        posix = interp.use("POSIX")
        interp.close()

        with pytest.raises(RuntimeError, match="closed"):
            interp.use("POSIX")

        with pytest.raises(RuntimeError, match="closed"):
            posix.floor(1.9)

    def test_nested_context_managers(self):
        with perlthon.interpreter() as outer:
            outer.eval('$main::nested_value = "outer"')

            with perlthon.interpreter() as inner:
                inner.eval('$main::nested_value = "inner"')

                assert inner.eval("$main::nested_value") == "inner"

            assert outer.eval("$main::nested_value") == "outer"
