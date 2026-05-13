"""Tests for Python-to-Perl callback registration."""

import pytest

import perlthon


class TestCallbacks:
    def test_register_simple_function(self):
        perlthon.register("MyApp::transform", lambda value: value.upper())
        assert perlthon.eval('MyApp::transform("hello")') == "HELLO"

    def test_register_decorator(self):
        @perlthon.register("Utils::double")
        def double(value):
            return value * 2

        assert perlthon.eval("Utils::double(21)") == 42
        assert double(10) == 20

    def test_callback_multiple_arguments(self):
        perlthon.register(
            "Math::combine", lambda left, right, suffix: f"{left}-{right}-{suffix}"
        )
        assert perlthon.eval('Math::combine("left", 7, "done")') == "left-7-done"

    @pytest.mark.parametrize(
        ("name", "value"),
        [
            ("Types::int_value", 42),
            ("Types::str_value", "hello"),
            ("Types::list_value", [1, "two", None]),
            ("Types::dict_value", {"name": "perlthon", "count": 3}),
            ("Types::none_value", None),
        ],
    )
    def test_callback_return_types(self, name, value):
        perlthon.register(name, lambda: value)
        assert perlthon.eval(f"{name}()") == value

    def test_callback_exception_becomes_die(self):
        def explode():
            raise ValueError("boom from python")

        perlthon.register("Errors::explode", explode)

        with pytest.raises(RuntimeError, match="boom from python"):
            perlthon.eval("Errors::explode()")

        assert perlthon.eval("40 + 2") == 42

    def test_callback_overwrite(self):
        perlthon.register("MyApp::status", lambda: "first")
        perlthon.register("MyApp::status", lambda: "second")
        assert perlthon.eval("MyApp::status()") == "second"

    def test_unregistered_name_raises_error(self):
        with pytest.raises(RuntimeError, match="Undefined subroutine"):
            perlthon.eval("Missing::callback()")
