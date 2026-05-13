"""Tests for Python-to-Perl callback registration."""

import gc
import os
import subprocess
import sys
import textwrap
import weakref
from pathlib import Path

import pytest

import perlthon
from perlthon._core import PerlInterpreter


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

    def test_callback_registry_isolated_per_interpreter(self):
        first = PerlInterpreter()
        second = PerlInterpreter()

        first.register_callback("Scoped::name", lambda: "first")
        second.register_callback("Scoped::name", lambda: "second")

        assert first.eval("Scoped::name()") == "first"
        assert second.eval("Scoped::name()") == "second"

    def test_register_uses_module_interpreter(self):
        assert perlthon.eval("40 + 2") == 42

        other = PerlInterpreter()
        assert other.eval("6 * 7") == 42

        perlthon.register("Scoped::global_name", lambda: "module")

        assert perlthon.eval("Scoped::global_name()") == "module"
        with pytest.raises(RuntimeError, match="Undefined subroutine"):
            other.eval("Scoped::global_name()")

    def test_register_validates_callback_names(self):
        with pytest.raises(ValueError, match="Invalid Perl function name"):
            perlthon.register("Bad Name", lambda: None)

        interp = PerlInterpreter()
        with pytest.raises(ValueError, match="Invalid Perl function name"):
            interp.register_callback("Bad Name", lambda: None)

    def test_callback_can_reenter_same_interpreter(self):
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
                    import perlthon

                    @perlthon.register("Reenter::callback")
                    def callback():
                        return perlthon.eval("41 + 1")

                    print(perlthon.eval("Reenter::callback()"))
                    """
                ),
            ],
            capture_output=True,
            check=False,
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "PYTHONPATH": pythonpath},
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "42"

    def test_callbacks_removed_when_interpreter_drops(self):
        class Callback:
            def __call__(self):
                return "ok"

        interp = PerlInterpreter()
        callback = Callback()
        callback_ref = weakref.ref(callback)

        interp.register_callback("Cleanup::callback", callback)
        del callback
        gc.collect()
        assert callback_ref() is not None

        del interp
        gc.collect()
        assert callback_ref() is None
