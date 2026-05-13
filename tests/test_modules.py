"""Tests for perlthon.modules — Python-style Perl module imports."""

import pytest

from perlthon.modules import _PerlNamespace


class TestNamespaceProxy:
    """Test the namespace proxy accumulation."""

    def test_single_segment(self):
        from perlthon import modules

        ns = modules.POSIX
        assert isinstance(ns, _PerlNamespace)
        assert repr(ns) == "PerlNamespace(POSIX)"

    def test_two_segments(self):
        from perlthon import modules

        ns = modules.File.Basename
        assert isinstance(ns, _PerlNamespace)
        assert repr(ns) == "PerlNamespace(File::Basename)"

    def test_three_segments(self):
        from perlthon import modules

        ns = modules.File.Basename.basename
        assert repr(ns) == "PerlNamespace(File::Basename::basename)"

    def test_double_underscore_remains_valid_identifier(self):
        from perlthon import modules

        ns = modules.Some__Module
        assert repr(ns) == "PerlNamespace(Some__Module)"

    def test_private_attr_raises(self):
        from perlthon import modules

        with pytest.raises(AttributeError):
            _ = modules._private


class TestModuleCalls:
    """Test calling Perl functions via the module proxy."""

    def test_posix_floor(self):
        from perlthon import modules

        result = modules.POSIX.floor(3.7)
        assert result == 3

    def test_posix_ceil(self):
        from perlthon import modules

        result = modules.POSIX.ceil(3.2)
        assert result == 4

    def test_file_basename(self):
        from perlthon import modules

        result = modules.File.Basename.basename("/usr/local/bin/perl")
        assert result == "perl"

    def test_file_dirname(self):
        from perlthon import modules

        result = modules.File.Basename.dirname("/usr/local/bin/perl")
        assert result == "/usr/local/bin"

    def test_list_util_sum(self):
        from perlthon import modules

        result = modules.List.Util.sum(1, 2, 3, 4, 5)
        assert result == 15

    def test_list_util_min(self):
        from perlthon import modules

        result = modules.List.Util.min(5, 3, 8, 1, 4)
        assert result == 1

    def test_list_util_max(self):
        from perlthon import modules

        result = modules.List.Util.max(5, 3, 8, 1, 4)
        assert result == 8

    def test_scalar_util_looks_like_number(self):
        from perlthon import modules

        assert modules.Scalar.Util.looks_like_number("42")
        assert modules.Scalar.Util.looks_like_number("3.14")
        assert not modules.Scalar.Util.looks_like_number("hello")

    def test_cwd(self):
        from perlthon import modules

        result = modules.Cwd.cwd()
        assert isinstance(result, str)
        assert len(result) > 0


class TestFromImport:
    """Test 'from perlthon.modules import X' style."""

    def test_from_import_posix(self):
        from perlthon.modules import POSIX

        assert POSIX.floor(2.9) == 2
        assert POSIX.ceil(2.1) == 3

    def test_from_import_file(self):
        from perlthon.modules import File

        result = File.Basename.basename("/tmp/foo.txt")
        assert result == "foo.txt"

    def test_from_import_list(self):
        from perlthon.modules import List

        assert List.Util.max(10, 20, 30) == 30

    def test_from_import_scalar(self):
        from perlthon.modules import Scalar

        assert Scalar.Util.looks_like_number("123")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_call_raises(self):
        ns = _PerlNamespace([])
        with pytest.raises(TypeError, match="Cannot call empty namespace"):
            ns()

    def test_nonexistent_module_raises(self):
        from perlthon import modules

        with pytest.raises(RuntimeError):
            modules.Totally.Fake.Module.nonexistent()

    def test_namespace_proxy_validates_module_names(self):
        namespace = _PerlNamespace(["Bad Module", "floor"])

        with pytest.raises(ValueError, match="Invalid Perl module name"):
            namespace()

    def test_namespace_proxy_validates_function_names(self):
        namespace = _PerlNamespace(["POSIX", "floor; print qq(INJECTED\\n)"])

        with pytest.raises(ValueError, match="Invalid Perl function name"):
            namespace(3.7)

    def test_multiple_calls_same_proxy(self):
        """Proxy is reusable — each call is independent."""
        from perlthon.modules import POSIX

        assert POSIX.floor(1.1) == 1
        assert POSIX.floor(2.9) == 2
        assert POSIX.floor(99.99) == 99

    def test_chained_different_modules(self):
        """Different modules can be used in sequence."""
        from perlthon import modules

        assert modules.POSIX.floor(3.7) == 3
        assert modules.List.Util.sum(1, 2, 3) == 6

    def test_proxy_is_not_module(self):
        """Namespace proxy is distinct from PerlModule."""
        from perlthon.modules import POSIX

        assert isinstance(POSIX, _PerlNamespace)
