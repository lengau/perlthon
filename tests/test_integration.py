"""Integration tests for perlthon using real Perl execution."""

import pytest

import perlthon


class TestEvalScalars:
    """Test eval with scalar return values."""

    def test_integer_arithmetic(self):
        assert perlthon.eval("2 + 3") == 5

    def test_negative_integer(self):
        assert perlthon.eval("-42") == -42

    def test_float_arithmetic(self):
        result = perlthon.eval("3.14 * 2")
        assert abs(result - 6.28) < 1e-10

    def test_string_concatenation(self):
        assert perlthon.eval('"foo" . "bar"') == "foobar"

    def test_string_repetition(self):
        assert perlthon.eval('"ab" x 3') == "ababab"

    def test_multiline_string(self):
        result = perlthon.eval('"line1\\nline2"')
        assert result == "line1\nline2"

    def test_empty_string(self):
        assert perlthon.eval('""') == ""

    def test_undef_returns_none(self):
        assert perlthon.eval("undef") is None

    def test_boolean_true(self):
        result = perlthon.eval("1 == 1")
        assert result == 1

    def test_boolean_false(self):
        result = perlthon.eval("1 == 0")
        # Perl false is empty string or 0
        assert not result

    def test_large_integer(self):
        assert perlthon.eval("2 ** 32") == 4294967296

    def test_string_length(self):
        assert perlthon.eval('length("hello")') == 5

    def test_sprintf(self):
        assert perlthon.eval('sprintf("%05d", 42)') == "00042"


class TestEvalDataStructures:
    """Test eval with array and hash references."""

    def test_array_ref_integers(self):
        assert perlthon.eval("[1, 2, 3, 4, 5]") == [1, 2, 3, 4, 5]

    def test_array_ref_strings(self):
        assert perlthon.eval('["a", "b", "c"]') == ["a", "b", "c"]

    def test_array_ref_mixed(self):
        result = perlthon.eval('[1, "two", 3.0]')
        assert result == [1, "two", 3.0]

    def test_array_ref_empty(self):
        assert perlthon.eval("[]") == []

    def test_nested_array_ref(self):
        assert perlthon.eval("[[1, 2], [3, 4]]") == [[1, 2], [3, 4]]

    def test_hash_ref(self):
        result = perlthon.eval('{"name" => "perl", "version" => 5}')
        assert result == {"name": "perl", "version": 5}

    def test_hash_ref_empty(self):
        assert perlthon.eval("{}") == {}

    def test_nested_hash_ref(self):
        result = perlthon.eval('{"inner" => {"key" => "val"}}')
        assert result == {"inner": {"key": "val"}}

    def test_hash_with_array_value(self):
        result = perlthon.eval('{"nums" => [1, 2, 3]}')
        assert result == {"nums": [1, 2, 3]}

    def test_array_with_hash_elements(self):
        result = perlthon.eval('[{"a" => 1}, {"b" => 2}]')
        assert result == [{"a": 1}, {"b": 2}]


class TestEvalControlFlow:
    """Test eval with Perl control flow and expressions."""

    def test_ternary(self):
        assert perlthon.eval("(5 > 3) ? 'yes' : 'no'") == "yes"

    def test_do_block(self):
        result = perlthon.eval("do { my $x = 10; $x * 2 }")
        assert result == 20

    def test_multiple_statements(self):
        code = "my $x = 5; my $y = 10; $x + $y"
        assert perlthon.eval(code) == 15

    def test_string_operations(self):
        assert perlthon.eval('uc("hello")') == "HELLO"

    def test_lc(self):
        assert perlthon.eval('lc("WORLD")') == "world"

    def test_reverse_string(self):
        assert perlthon.eval('scalar reverse "abcde"') == "edcba"

    def test_chomp_equivalent(self):
        code = 'do { my $s = "hello\\n"; chomp $s; $s }'
        assert perlthon.eval(code) == "hello"

    def test_regex_match(self):
        code = 'do { "hello world" =~ /^(\\w+)/; $1 }'
        assert perlthon.eval(code) == "hello"

    def test_regex_substitution(self):
        code = 'do { my $s = "foo bar"; $s =~ s/foo/baz/; $s }'
        assert perlthon.eval(code) == "baz bar"

    def test_map(self):
        result = perlthon.eval("[map { $_ * 2 } (1, 2, 3)]")
        assert result == [2, 4, 6]

    def test_grep(self):
        result = perlthon.eval("[grep { $_ > 2 } (1, 2, 3, 4, 5)]")
        assert result == [3, 4, 5]

    def test_sort(self):
        result = perlthon.eval("[sort { $a <=> $b } (3, 1, 4, 1, 5)]")
        assert result == [1, 1, 3, 4, 5]

    def test_join(self):
        assert perlthon.eval('join(", ", "a", "b", "c")') == "a, b, c"

    def test_split(self):
        result = perlthon.eval('[split(/,/, "a,b,c")]')
        assert result == ["a", "b", "c"]


class TestEvalErrors:
    """Test that Perl errors propagate as Python exceptions."""

    def test_syntax_error(self):
        with pytest.raises(RuntimeError):
            perlthon.eval("if (")

    def test_die(self):
        with pytest.raises(RuntimeError):
            perlthon.eval('die "something went wrong"')

    def test_strict_violation(self):
        with pytest.raises(RuntimeError):
            perlthon.eval("use strict; $undefined_var")


class TestUseModule:
    """Test loading Perl modules."""

    def test_use_posix(self):
        mod = perlthon.use("POSIX")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_scalar_util(self):
        mod = perlthon.use("Scalar::Util")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_file_basename(self):
        mod = perlthon.use("File::Basename")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_list_util(self):
        mod = perlthon.use("List::Util")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_nonexistent_raises(self):
        with pytest.raises(RuntimeError):
            perlthon.use("Completely::Fake::Module::XYZ")

    def test_use_invalid_name_raises(self):
        with pytest.raises(RuntimeError):
            perlthon.use("")

    def test_module_repr(self):
        mod = perlthon.use("POSIX")
        assert "POSIX" in repr(mod)


class TestCallFunction:
    """Test calling Perl functions by fully qualified name."""

    def test_posix_floor(self):
        perlthon.use("POSIX")
        assert perlthon.call("POSIX::floor", 3.7) == 3.0

    def test_posix_ceil(self):
        perlthon.use("POSIX")
        assert perlthon.call("POSIX::ceil", 3.2) == 4.0

    def test_posix_fmod(self):
        perlthon.use("POSIX")
        result = perlthon.call("POSIX::fmod", 10.0, 3.0)
        assert abs(result - 1.0) < 1e-10

    def test_file_basename(self):
        perlthon.use("File::Basename")
        result = perlthon.call("File::Basename::basename", "/usr/local/bin/perl")
        assert result == "perl"

    def test_file_dirname(self):
        perlthon.use("File::Basename")
        result = perlthon.call("File::Basename::dirname", "/usr/local/bin/perl")
        assert result == "/usr/local/bin"

    def test_scalar_util_looks_like_number(self):
        perlthon.use("Scalar::Util")
        assert perlthon.call("Scalar::Util::looks_like_number", "42")
        assert not perlthon.call("Scalar::Util::looks_like_number", "abc")

    def test_list_util_sum(self):
        perlthon.use("List::Util")
        result = perlthon.call("List::Util::sum", 1, 2, 3, 4, 5)
        assert result == 15

    def test_list_util_min(self):
        perlthon.use("List::Util")
        assert perlthon.call("List::Util::min", 5, 2, 8, 1, 9) == 1

    def test_list_util_max(self):
        perlthon.use("List::Util")
        assert perlthon.call("List::Util::max", 5, 2, 8, 1, 9) == 9


class TestPerlModuleMethods:
    """Test calling methods on PerlModule objects."""

    def test_posix_floor_method(self):
        posix = perlthon.use("POSIX")
        assert posix.floor(9.9) == 9.0

    def test_posix_ceil_method(self):
        posix = perlthon.use("POSIX")
        assert posix.ceil(0.1) == 1.0

    def test_posix_pow_method(self):
        posix = perlthon.use("POSIX")
        assert posix.pow(2, 10) == 1024.0

    def test_posix_sqrt_method(self):
        posix = perlthon.use("POSIX")
        result = posix.sqrt(144.0)
        assert abs(result - 12.0) < 1e-10

    def test_file_basename_method(self):
        fb = perlthon.use("File::Basename")
        assert fb.basename("/home/user/file.txt") == "file.txt"

    def test_file_dirname_method(self):
        fb = perlthon.use("File::Basename")
        assert fb.dirname("/home/user/file.txt") == "/home/user"

    def test_cwd_module(self):
        cwd = perlthon.use("Cwd")
        result = cwd.cwd()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_list_util_methods(self):
        lu = perlthon.use("List::Util")
        assert lu.sum(10, 20, 30) == 60
        assert lu.min(10, 20, 30) == 10
        assert lu.max(10, 20, 30) == 30

    def test_callable_repr(self):
        posix = perlthon.use("POSIX")
        callable_obj = posix.floor
        assert "POSIX" in repr(callable_obj)
        assert "floor" in repr(callable_obj)


class TestTypeConversions:
    """Test Python-to-Perl and Perl-to-Python type conversions."""

    def test_pass_int(self):
        perlthon.use("POSIX")
        assert perlthon.call("POSIX::floor", 5) == 5.0

    def test_pass_float(self):
        perlthon.use("POSIX")
        assert perlthon.call("POSIX::ceil", 2.1) == 3.0

    def test_pass_string(self):
        perlthon.use("File::Basename")
        result = perlthon.call("File::Basename::basename", "/path/to/file")
        assert result == "file"

    def test_pass_negative(self):
        perlthon.use("POSIX")
        assert perlthon.call("POSIX::floor", -2.3) == -3.0

    def test_pass_zero(self):
        perlthon.use("POSIX")
        assert perlthon.call("POSIX::floor", 0.0) == 0.0

    def test_return_string_with_unicode(self):
        result = perlthon.eval('use utf8; "café"')
        assert result == "café"

    def test_return_large_list(self):
        result = perlthon.eval("[1..100]")
        assert len(result) == 100
        assert result[0] == 1
        assert result[99] == 100

    def test_return_hash_multiple_keys(self):
        result = perlthon.eval(
            'do { my %h = (a => 1, b => 2, c => 3, d => 4, e => 5);'
            ' +{%h} }'
        )
        assert isinstance(result, dict)
        assert len(result) == 5


class TestMultipleModules:
    """Test using multiple modules together."""

    def test_use_multiple_modules(self):
        posix = perlthon.use("POSIX")
        fb = perlthon.use("File::Basename")
        assert posix.floor(1.5) == 1.0
        assert fb.basename("/tmp/test.txt") == "test.txt"

    def test_modules_independent(self):
        lu = perlthon.use("List::Util")
        su = perlthon.use("Scalar::Util")
        assert lu.sum(1, 2, 3) == 6
        assert su.looks_like_number("3.14")

    def test_eval_after_use(self):
        perlthon.use("POSIX")
        result = perlthon.eval("POSIX::floor(7.9)")
        assert result == 7.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_eval_whitespace_only(self):
        result = perlthon.eval("   ")
        # Whitespace evaluates to empty/undef
        assert not result

    def test_eval_comment_only(self):
        result = perlthon.eval("# just a comment\n42")
        assert result == 42

    def test_deeply_nested(self):
        result = perlthon.eval('{"a" => {"b" => {"c" => [1, 2, 3]}}}')
        assert result == {"a": {"b": {"c": [1, 2, 3]}}}

    def test_special_characters_in_string(self):
        result = perlthon.eval('"hello\\tworld"')
        assert result == "hello\tworld"

    def test_empty_array_ref(self):
        assert perlthon.eval("[]") == []

    def test_single_element_array(self):
        assert perlthon.eval("[42]") == [42]

    def test_repeated_eval(self):
        for i in range(50):
            assert perlthon.eval(f"{i} + 1") == i + 1

    def test_repeated_module_use(self):
        # Using the same module multiple times should be fine
        for _ in range(10):
            mod = perlthon.use("POSIX")
            assert mod.floor(1.5) == 1.0
