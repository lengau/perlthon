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

    def test_integer_subtraction(self):
        assert perlthon.eval("100 - 37") == 63

    def test_integer_multiplication(self):
        assert perlthon.eval("7 * 8") == 56

    def test_integer_division(self):
        assert perlthon.eval("int(17 / 3)") == 5

    def test_modulo(self):
        assert perlthon.eval("17 % 5") == 2

    def test_exponentiation(self):
        assert perlthon.eval("2 ** 10") == 1024

    def test_very_large_integer(self):
        assert perlthon.eval("2 ** 53") == 9007199254740992

    def test_float_division(self):
        result = perlthon.eval("22 / 7")
        assert abs(result - 3.142857142857) < 1e-6

    def test_negative_float(self):
        result = perlthon.eval("-3.14")
        assert abs(result - (-3.14)) < 1e-10

    def test_scientific_notation(self):
        result = perlthon.eval("1.5e3")
        assert result == 1500.0

    def test_hex_literal(self):
        assert perlthon.eval("0xFF") == 255

    def test_octal_literal(self):
        assert perlthon.eval("0777") == 511

    def test_binary_literal(self):
        assert perlthon.eval("0b11111111") == 255

    def test_string_with_spaces(self):
        assert perlthon.eval('"  hello  "') == "  hello  "

    def test_string_with_newlines(self):
        assert perlthon.eval('"a\\nb\\nc"') == "a\nb\nc"

    def test_string_with_tab(self):
        assert perlthon.eval('"col1\\tcol2"') == "col1\tcol2"

    def test_string_with_null_char(self):
        result = perlthon.eval('"a\\x00b"')
        assert len(result) == 3

    def test_single_char(self):
        assert perlthon.eval('"x"') == "x"

    def test_numeric_string(self):
        result = perlthon.eval('"42"')
        assert result == "42"

    def test_chr_function(self):
        assert perlthon.eval("chr(65)") == "A"

    def test_ord_function(self):
        assert perlthon.eval('ord("A")') == 65

    def test_abs_positive(self):
        assert perlthon.eval("abs(42)") == 42

    def test_abs_negative(self):
        assert perlthon.eval("abs(-42)") == 42

    def test_int_truncation(self):
        assert perlthon.eval("int(9.99)") == 9

    def test_int_negative_truncation(self):
        assert perlthon.eval("int(-9.99)") == -9

    def test_zero(self):
        assert perlthon.eval("0") == 0

    def test_zero_float(self):
        result = perlthon.eval("0.0")
        assert result == 0


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

    def test_large_array(self):
        result = perlthon.eval("[1..1000]")
        assert len(result) == 1000
        assert result[0] == 1
        assert result[999] == 1000

    def test_array_of_empty_strings(self):
        result = perlthon.eval('["", "", ""]')
        assert result == ["", "", ""]

    def test_array_with_undef(self):
        result = perlthon.eval("[1, undef, 3]")
        assert result[0] == 1
        assert result[1] is None
        assert result[2] == 3

    def test_hash_with_numeric_values(self):
        result = perlthon.eval('{"pi" => 3.14, "e" => 2.72}')
        assert abs(result["pi"] - 3.14) < 1e-10
        assert abs(result["e"] - 2.72) < 1e-10

    def test_hash_with_undef_value(self):
        result = perlthon.eval('{"key" => undef}')
        assert result == {"key": None}

    def test_deeply_nested_array(self):
        result = perlthon.eval("[[[[[1]]]]]")
        assert result == [[[[[1]]]]]

    def test_array_with_negative_numbers(self):
        result = perlthon.eval("[-5, -3, -1, 0, 1, 3, 5]")
        assert result == [-5, -3, -1, 0, 1, 3, 5]

    def test_hash_many_keys(self):
        code = "do { my %h; $h{$_} = $_ * 2 for 1..26; +{%h} }"
        result = perlthon.eval(code)
        assert isinstance(result, dict)
        assert len(result) == 26

    def test_array_of_arrays(self):
        result = perlthon.eval("[[1,2,3],[4,5,6],[7,8,9]]")
        assert result == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    def test_hash_of_arrays(self):
        result = perlthon.eval('{"odd" => [1,3,5], "even" => [2,4,6]}')
        assert result == {"odd": [1, 3, 5], "even": [2, 4, 6]}

    def test_complex_nested_structure(self):
        code = """
        {
            "users" => [
                {"name" => "alice", "age" => 30},
                {"name" => "bob", "age" => 25}
            ],
            "count" => 2
        }
        """
        result = perlthon.eval(code)
        assert result["count"] == 2
        assert len(result["users"]) == 2
        assert result["users"][0]["name"] == "alice"
        assert result["users"][1]["age"] == 25


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

    def test_for_loop(self):
        code = "do { my $sum = 0; $sum += $_ for 1..10; $sum }"
        assert perlthon.eval(code) == 55

    def test_while_loop(self):
        code = "do { my $i = 0; my $s = 0; while ($i < 5) { $s += $i; $i++ } $s }"
        assert perlthon.eval(code) == 10

    def test_unless(self):
        code = 'do { my $x = "yes"; $x = "no" unless 1; $x }'
        assert perlthon.eval(code) == "yes"

    def test_until_loop(self):
        code = "do { my $i = 0; $i++ until $i >= 5; $i }"
        assert perlthon.eval(code) == 5

    def test_if_elsif_else(self):
        code = """
        do {
            my $x = 15;
            if ($x > 20) { "big" }
            elsif ($x > 10) { "medium" }
            else { "small" }
        }
        """
        assert perlthon.eval(code) == "medium"

    def test_string_eq(self):
        assert perlthon.eval('"hello" eq "hello" ? 1 : 0') == 1

    def test_string_ne(self):
        assert perlthon.eval('"hello" ne "world" ? 1 : 0') == 1

    def test_string_lt(self):
        assert perlthon.eval('"apple" lt "banana" ? 1 : 0') == 1

    def test_chained_string_ops(self):
        code = 'join("-", map { uc($_) } split(/\\s+/, "hello world foo"))'
        assert perlthon.eval(code) == "HELLO-WORLD-FOO"

    def test_regex_global_match(self):
        code = 'do { my @m = ("abc123def456" =~ /(\\d+)/g); \\@m }'
        result = perlthon.eval(code)
        assert result == ["123", "456"]

    def test_regex_global_substitution(self):
        code = 'do { my $s = "aabaa"; $s =~ s/a/x/g; $s }'
        assert perlthon.eval(code) == "xxbxx"

    def test_heredoc(self):
        code = "do { my $s = <<END;\nhello\nworld\nEND\nchomp $s; $s }"
        assert perlthon.eval(code) == "hello\nworld"

    def test_wantarray_scalar_context(self):
        code = "scalar @{[1,2,3,4,5]}"
        assert perlthon.eval(code) == 5

    def test_substr(self):
        assert perlthon.eval('substr("Hello World", 6, 5)') == "World"

    def test_index(self):
        assert perlthon.eval('index("Hello World", "World")') == 6

    def test_rindex(self):
        assert perlthon.eval('rindex("abcabc", "abc")') == 3

    def test_sprintf_float(self):
        assert perlthon.eval('sprintf("%.2f", 3.14159)') == "3.14"

    def test_sprintf_hex(self):
        assert perlthon.eval('sprintf("%x", 255)') == "ff"

    def test_pack_unpack(self):
        code = 'do { my $packed = pack("N", 12345); unpack("N", $packed) }'
        assert perlthon.eval(code) == 12345

    def test_sort_strings(self):
        result = perlthon.eval('[sort ("banana", "apple", "cherry")]')
        assert result == ["apple", "banana", "cherry"]

    def test_reverse_array(self):
        result = perlthon.eval("[reverse 1..5]")
        assert result == [5, 4, 3, 2, 1]

    def test_map_with_grep(self):
        code = "[map { $_ ** 2 } grep { $_ % 2 == 0 } 1..10]"
        result = perlthon.eval(code)
        assert result == [4, 16, 36, 64, 100]

    def test_array_slice(self):
        code = 'do { my @a = ("a".."z"); [@a[0,4,8,14,20]] }'
        result = perlthon.eval(code)
        assert result == ["a", "e", "i", "o", "u"]

    def test_hash_slice(self):
        code = "do { my %h = (a=>1,b=>2,c=>3,d=>4); [@h{qw(a c d)}] }"
        result = perlthon.eval(code)
        assert result == [1, 3, 4]

    def test_local_variable_scope(self):
        code = """
        do {
            my $x = "outer";
            my $result;
            {
                my $x = "inner";
                $result = $x;
            }
            $result
        }
        """
        assert perlthon.eval(code) == "inner"

    def test_closures(self):
        code = """
        do {
            my $make_adder = sub { my $n = shift; sub { $n + shift } };
            my $add5 = $make_adder->(5);
            $add5->(10)
        }
        """
        assert perlthon.eval(code) == 15

    def test_anonymous_sub(self):
        code = "do { my $double = sub { $_[0] * 2 }; $double->(21) }"
        assert perlthon.eval(code) == 42

    def test_array_push_pop(self):
        code = "do { my @a = (1,2,3); push @a, 4, 5; pop @a; \\@a }"
        result = perlthon.eval(code)
        assert result == [1, 2, 3, 4]

    def test_array_shift_unshift(self):
        code = "do { my @a = (1,2,3); unshift @a, 0; shift @a; \\@a }"
        result = perlthon.eval(code)
        assert result == [1, 2, 3]

    def test_array_splice(self):
        code = "do { my @a = (1,2,3,4,5); splice(@a, 1, 2); \\@a }"
        result = perlthon.eval(code)
        assert result == [1, 4, 5]

    def test_hash_exists(self):
        code = "do { my %h = (a => 1); exists $h{a} ? 1 : 0 }"
        assert perlthon.eval(code) == 1

    def test_hash_delete(self):
        code = "do { my %h = (a => 1, b => 2); delete $h{a}; +{%h} }"
        result = perlthon.eval(code)
        assert result == {"b": 2}

    def test_hash_keys(self):
        code = "do { my %h = (a => 1, b => 2, c => 3); scalar keys %h }"
        assert perlthon.eval(code) == 3

    def test_wantarray_list_context(self):
        code = "[keys %{{a => 1, b => 2, c => 3}}]"
        result = perlthon.eval(code)
        assert sorted(result) == ["a", "b", "c"]


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

    def test_die_with_reference(self):
        with pytest.raises(RuntimeError):
            perlthon.eval('die { code => 404, message => "not found" }')

    def test_croak(self):
        with pytest.raises(RuntimeError):
            perlthon.eval('use Carp; croak "something bad"')

    def test_division_by_zero(self):
        with pytest.raises(RuntimeError):
            perlthon.eval("do { use warnings FATAL => 'all'; 1/0 }")

    def test_undefined_function(self):
        with pytest.raises(RuntimeError):
            perlthon.eval("no_such_function_xyz()")

    def test_require_nonexistent(self):
        with pytest.raises(RuntimeError):
            perlthon.eval('require "nonexistent_file_xyz.pl"')

    def test_die_in_eval_block(self):
        # Perl's eval {} catches the die, so no Python error
        result = perlthon.eval('do { eval { die "caught" }; $@ ? "error" : "ok" }')
        assert result == "error"

    def test_warn_does_not_raise(self):
        # warn should not raise a Python exception
        result = perlthon.eval('do { warn "just a warning"; 42 }')
        assert result == 42

    def test_nested_die(self):
        with pytest.raises(RuntimeError, match="inner"):
            perlthon.eval('die "inner error"')


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

    def test_use_cwd(self):
        mod = perlthon.use("Cwd")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_file_path(self):
        mod = perlthon.use("File::Path")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_file_spec(self):
        mod = perlthon.use("File::Spec")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_file_temp(self):
        mod = perlthon.use("File::Temp")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_data_dumper(self):
        mod = perlthon.use("Data::Dumper")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_storable(self):
        mod = perlthon.use("Storable")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_digest_md5(self):
        mod = perlthon.use("Digest::MD5")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_encode(self):
        mod = perlthon.use("Encode")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_json_pp(self):
        mod = perlthon.use("JSON::PP")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_time_piece(self):
        mod = perlthon.use("Time::Piece")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_mime_base64(self):
        mod = perlthon.use("MIME::Base64")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_io_file(self):
        mod = perlthon.use("IO::File")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_socket(self):
        mod = perlthon.use("Socket")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_fcntl(self):
        mod = perlthon.use("Fcntl")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_text_parsewords(self):
        mod = perlthon.use("Text::ParseWords")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_getopt_long(self):
        mod = perlthon.use("Getopt::Long")
        assert isinstance(mod, perlthon.PerlModule)

    def test_use_math_bigint(self):
        mod = perlthon.use("Math::BigInt")
        assert isinstance(mod, perlthon.PerlModule)


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

    def test_mime_base64_encode(self):
        perlthon.use("MIME::Base64")
        result = perlthon.call("MIME::Base64::encode_base64", "hello", "")
        assert result == "aGVsbG8="

    def test_mime_base64_decode(self):
        perlthon.use("MIME::Base64")
        result = perlthon.call("MIME::Base64::decode_base64", "aGVsbG8=")
        assert result == "hello"

    def test_digest_md5_hex(self):
        perlthon.use("Digest::MD5")
        result = perlthon.call("Digest::MD5::md5_hex", "hello")
        assert result == "5d41402abc4b2a76b9719d911017c592"

    def test_file_spec_catfile(self):
        perlthon.use("File::Spec::Functions")
        result = perlthon.call("File::Spec::Functions::catfile", "/usr", "local", "bin")
        assert result == "/usr/local/bin"

    def test_scalar_util_blessed_undef(self):
        perlthon.use("Scalar::Util")
        result = perlthon.call("Scalar::Util::blessed", "not_a_ref")
        # blessed on a non-reference returns undef
        assert result is None

    def test_list_util_reduce(self):
        perlthon.use("List::Util")
        # reduce needs a code block, use eval instead
        result = perlthon.eval(
            'do { use List::Util "reduce"; reduce { $a + $b } 1, 2, 3, 4, 5 }'
        )
        assert result == 15

    def test_list_util_first(self):
        perlthon.use("List::Util")
        result = perlthon.eval(
            'do { use List::Util "first"; first { $_ > 3 } 1, 2, 3, 4, 5 }'
        )
        assert result == 4

    def test_posix_strftime(self):
        perlthon.use("POSIX")
        # Use a fixed time to get a deterministic result
        result = perlthon.eval('POSIX::strftime("%Y", localtime(0))')
        assert result == "1970"

    def test_cwd(self):
        perlthon.use("Cwd")
        result = perlthon.call("Cwd::cwd")
        assert isinstance(result, str)
        assert len(result) > 0


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

    def test_posix_fabs(self):
        posix = perlthon.use("POSIX")
        assert posix.fabs(-42.5) == 42.5

    def test_posix_log(self):
        posix = perlthon.use("POSIX")
        import math

        result = posix.log(math.e)
        assert abs(result - 1.0) < 1e-10

    def test_posix_exp(self):
        posix = perlthon.use("POSIX")
        result = posix.exp(1.0)
        assert abs(result - 2.718281828) < 1e-6

    def test_file_basename_fileparse(self):
        fb = perlthon.use("File::Basename")
        # fileparse returns list, but we call as function
        # — only gets first in scalar context
        result = fb.basename("/path/to/file.txt")
        assert result == "file.txt"

    def test_list_util_product(self):
        lu = perlthon.use("List::Util")
        assert lu.product(2, 3, 4, 5) == 120

    def test_list_util_any(self):
        # any needs a block, use eval
        result = perlthon.eval(
            'do { use List::Util "any"; any { $_ > 3 } 1, 2, 3, 4, 5 }'
        )
        assert result

    def test_list_util_all(self):
        result = perlthon.eval(
            'do { use List::Util "all"; all { $_ > 0 } 1, 2, 3, 4, 5 }'
        )
        assert result

    def test_list_util_none(self):
        result = perlthon.eval(
            'do { use List::Util "none"; none { $_ > 10 } 1, 2, 3, 4, 5 }'
        )
        assert result


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
            "do { my %h = (a => 1, b => 2, c => 3, d => 4, e => 5); +{%h} }"
        )
        assert isinstance(result, dict)
        assert len(result) == 5

    def test_pass_empty_string(self):
        perlthon.use("MIME::Base64")
        result = perlthon.call("MIME::Base64::encode_base64", "", "")
        assert result == ""

    def test_pass_large_integer(self):
        perlthon.use("POSIX")
        result = perlthon.call("POSIX::floor", 999999999.9)
        assert result == 999999999.0

    def test_pass_very_small_float(self):
        perlthon.use("POSIX")
        result = perlthon.call("POSIX::ceil", 0.0000001)
        assert result == 1.0

    def test_pass_negative_zero(self):
        perlthon.use("POSIX")
        result = perlthon.call("POSIX::floor", -0.0)
        assert result == 0.0

    def test_return_unicode_emoji(self):
        result = perlthon.eval('use utf8; "\\x{1F600}"')
        assert result == "\U0001f600"

    def test_return_binary_data(self):
        result = perlthon.eval('"\\x01\\x02\\x03"')
        assert len(result) == 3

    def test_string_with_quotes(self):
        result = perlthon.eval("'he said \"hi\"'")
        assert result == 'he said "hi"'

    def test_string_with_backslash(self):
        result = perlthon.eval('"C:\\\\Users\\\\test"')
        assert result == "C:\\Users\\test"

    def test_numeric_string_stays_string(self):
        # When Perl returns a string that looks like a number
        result = perlthon.eval('sprintf("%03d", 7)')
        assert result == "007"
        assert isinstance(result, str)

    def test_very_long_string(self):
        result = perlthon.eval('"x" x 10000')
        assert len(result) == 10000
        assert result == "x" * 10000


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

    def test_cross_module_data(self):
        perlthon.use("MIME::Base64")
        perlthon.use("Digest::MD5")
        # Encode a hash, decode it back
        encoded = perlthon.call("MIME::Base64::encode_base64", "test data", "")
        decoded = perlthon.call("MIME::Base64::decode_base64", encoded)
        assert decoded == "test data"

    def test_five_modules_loaded(self):
        mods = [
            perlthon.use("POSIX"),
            perlthon.use("List::Util"),
            perlthon.use("Scalar::Util"),
            perlthon.use("File::Basename"),
            perlthon.use("MIME::Base64"),
        ]
        assert all(isinstance(m, perlthon.PerlModule) for m in mods)

    def test_json_pp_encode_decode(self):
        perlthon.use("JSON::PP")
        encoded = perlthon.eval(
            'do { use JSON::PP; encode_json({name => "test", value => 42}) }'
        )
        assert '"name"' in encoded
        assert '"test"' in encoded

    def test_data_dumper_output(self):
        perlthon.use("Data::Dumper")
        result = perlthon.eval(
            "do { use Data::Dumper; "
            "local $Data::Dumper::Indent = 0; "
            "local $Data::Dumper::Terse = 1; "
            "Dumper([1,2,3]) }"
        )
        assert "1" in result
        assert "2" in result
        assert "3" in result


class TestPerlSubroutines:
    """Test defining and calling Perl subroutines."""

    def test_define_and_call_sub(self):
        perlthon.eval("sub my_add { return $_[0] + $_[1] }")
        result = perlthon.call("main::my_add", 3, 4)
        assert result == 7

    def test_recursive_sub(self):
        perlthon.eval("""
            sub my_factorial {
                my $n = shift;
                return 1 if $n <= 1;
                return $n * my_factorial($n - 1);
            }
        """)
        assert perlthon.call("main::my_factorial", 10) == 3628800

    def test_sub_with_default_args(self):
        perlthon.eval("""
            sub my_greet {
                my ($name, $greeting) = @_;
                $greeting //= "Hello";
                return "$greeting, $name!";
            }
        """)
        assert perlthon.call("main::my_greet", "World") == "Hello, World!"
        assert perlthon.call("main::my_greet", "World", "Hi") == "Hi, World!"

    def test_sub_returning_arrayref(self):
        perlthon.eval("""
            sub my_range {
                my ($start, $end) = @_;
                return [$start..$end];
            }
        """)
        result = perlthon.call("main::my_range", 1, 5)
        assert result == [1, 2, 3, 4, 5]

    def test_sub_returning_hashref(self):
        perlthon.eval("""
            sub my_person {
                my ($name, $age) = @_;
                return { name => $name, age => $age };
            }
        """)
        result = perlthon.call("main::my_person", "Alice", 30)
        assert result == {"name": "Alice", "age": 30}

    def test_sub_with_closure(self):
        perlthon.eval("""
            do {
                my $counter = 0;
                sub my_increment { return ++$counter }
                sub my_get_count { return $counter }
            }
        """)
        perlthon.call("main::my_increment")
        perlthon.call("main::my_increment")
        perlthon.call("main::my_increment")
        assert perlthon.call("main::my_get_count") == 3

    def test_sub_string_processing(self):
        perlthon.eval("""
            sub my_titlecase {
                my $s = shift;
                $s =~ s/\\b(\\w)/\\u$1/g;
                return $s;
            }
        """)
        result = perlthon.call("main::my_titlecase", "hello world foo bar")
        assert result == "Hello World Foo Bar"

    def test_sub_fibonacci(self):
        perlthon.eval("""
            sub my_fib {
                my $n = shift;
                my @fib = (0, 1);
                for my $i (2..$n) {
                    push @fib, $fib[-1] + $fib[-2];
                }
                return $fib[$n];
            }
        """)
        assert perlthon.call("main::my_fib", 10) == 55
        assert perlthon.call("main::my_fib", 20) == 6765


class TestPerlOOP:
    """Test Perl object-oriented programming patterns."""

    def test_class_method_call(self):
        perlthon.eval("""
            package MyClass;
            sub new { bless {}, shift }
            sub greet { return "hello from MyClass" }
            package main;
        """)
        result = perlthon.eval("MyClass->greet()")
        assert result == "hello from MyClass"

    def test_constructor_and_method(self):
        perlthon.eval("""
            package Counter;
            sub new {
                my ($class, %args) = @_;
                bless { count => $args{start} // 0 }, $class;
            }
            sub increment {
                my $self = shift;
                $self->{count}++;
                return $self->{count};
            }
            sub get_count {
                my $self = shift;
                return $self->{count};
            }
            package main;
        """)
        result = perlthon.eval("""
            do {
                my $c = Counter->new(start => 5);
                $c->increment();
                $c->increment();
                $c->get_count();
            }
        """)
        assert result == 7

    def test_inheritance(self):
        perlthon.eval("""
            package Animal;
            sub new { bless { name => $_[1] }, $_[0] }
            sub speak { return "..." }
            sub name { return $_[0]->{name} }

            package Dog;
            our @ISA = ('Animal');
            sub speak { return "Woof!" }

            package Cat;
            our @ISA = ('Animal');
            sub speak { return "Meow!" }

            package main;
        """)
        assert perlthon.eval('Dog->new("Rex")->speak()') == "Woof!"
        assert perlthon.eval('Cat->new("Whiskers")->speak()') == "Meow!"
        assert perlthon.eval('Dog->new("Rex")->name()') == "Rex"

    def test_method_chaining(self):
        perlthon.eval("""
            package Builder;
            sub new { bless { parts => [] }, shift }
            sub add {
                my ($self, $part) = @_;
                push @{$self->{parts}}, $part;
                return $self;
            }
            sub build {
                my $self = shift;
                return join(" ", @{$self->{parts}});
            }
            package main;
        """)
        result = perlthon.eval(
            'Builder->new->add("hello")->add("world")->add("!")->build()'
        )
        assert result == "hello world !"


class TestPerlRegex:
    """Test Perl regular expression capabilities."""

    def test_simple_match(self):
        result = perlthon.eval('"Hello World" =~ /World/ ? 1 : 0')
        assert result == 1

    def test_case_insensitive(self):
        result = perlthon.eval('"Hello" =~ /hello/i ? 1 : 0')
        assert result == 1

    def test_capture_groups(self):
        result = perlthon.eval(
            'do { "2024-01-15" =~ /(\\d{4})-(\\d{2})-(\\d{2})/; [$1, $2, $3] }'
        )
        assert result == ["2024", "01", "15"]

    def test_named_captures(self):
        result = perlthon.eval("""
            do {
                "John Smith" =~ /(?<first>\\w+) (?<last>\\w+)/;
                +{ first => $+{first}, last => $+{last} }
            }
        """)
        assert result == {"first": "John", "last": "Smith"}

    def test_global_match_count(self):
        result = perlthon.eval("""
            do {
                my @matches = ("aabbaab" =~ /a+/g);
                scalar @matches
            }
        """)
        # "aabbaab" has "aa" and "a" = 2 matches of /a+/
        assert result == 2

    def test_substitution_with_eval(self):
        result = perlthon.eval("""
            do {
                my $s = "1 + 2 = ?";
                $s =~ s/(\\d+) \\+ (\\d+)/$1 + $2/e;
                $s
            }
        """)
        assert result == "3 = ?"

    def test_split_with_regex(self):
        result = perlthon.eval('[split(/\\s*,\\s*/, "a , b , c")]')
        assert result == ["a", "b", "c"]

    def test_lookahead(self):
        result = perlthon.eval("""
            do {
                my @m = ("foobar foobaz" =~ /foo(?=bar)/g);
                scalar @m
            }
        """)
        assert result == 1

    def test_lookbehind(self):
        result = perlthon.eval("""
            do {
                "100USD 200EUR" =~ /(?<=\\d{3})(\\w+)/;
                $1
            }
        """)
        assert result == "USD"

    def test_non_greedy(self):
        result = perlthon.eval("""
            do {
                "<a><b><c>" =~ /^<(.+?)>/;
                $1
            }
        """)
        assert result == "a"

    def test_multiline_regex(self):
        result = perlthon.eval("""
            do {
                my $text = "line1\\nline2\\nline3";
                my @lines = ($text =~ /^(line\\d)$/mg);
                \\@lines
            }
        """)
        assert result == ["line1", "line2", "line3"]

    def test_regex_replace_all(self):
        result = perlthon.eval("""
            do {
                my $s = "the cat sat on the mat";
                $s =~ s/\\b(\\w)/\\U$1/g;
                $s
            }
        """)
        assert result == "The Cat Sat On The Mat"


class TestPerlStringOps:
    """Test Perl string manipulation functions."""

    def test_chomp(self):
        result = perlthon.eval('do { my $s = "hello\\n"; chomp $s; $s }')
        assert result == "hello"

    def test_chop(self):
        result = perlthon.eval('do { my $s = "hello"; chop $s; $s }')
        assert result == "hell"

    def test_substr_extraction(self):
        assert perlthon.eval('substr("Hello World", 0, 5)') == "Hello"

    def test_substr_negative(self):
        assert perlthon.eval('substr("Hello World", -5)') == "World"

    def test_uc_lc_ucfirst_lcfirst(self):
        assert perlthon.eval('uc("hello")') == "HELLO"
        assert perlthon.eval('lc("HELLO")') == "hello"
        assert perlthon.eval('ucfirst("hello")') == "Hello"
        assert perlthon.eval('lcfirst("HELLO")') == "hELLO"

    def test_quotemeta(self):
        result = perlthon.eval('quotemeta("hello.world")')
        assert "\\." in result

    def test_sprintf_various(self):
        assert perlthon.eval('sprintf("%d", 42)') == "42"
        assert perlthon.eval('sprintf("%08b", 42)') == "00101010"
        assert perlthon.eval('sprintf("%e", 12345.6789)') == "1.234568e+04"
        assert perlthon.eval('sprintf("%-10s|", "left")') == "left      |"

    def test_tr_operator(self):
        result = perlthon.eval('do { my $s = "hello"; $s =~ tr/a-z/A-Z/; $s }')
        assert result == "HELLO"

    def test_tr_count(self):
        result = perlthon.eval('do { my $s = "hello world"; $s =~ tr/l// }')
        assert result == 3

    def test_repeat_string(self):
        assert perlthon.eval('"abc" x 4') == "abcabcabcabc"

    def test_string_comparison_operators(self):
        assert perlthon.eval('"abc" lt "abd" ? 1 : 0') == 1
        assert perlthon.eval('"abc" gt "abb" ? 1 : 0') == 1
        assert perlthon.eval('"abc" eq "abc" ? 1 : 0') == 1
        assert perlthon.eval('"abc" cmp "abd"') == -1


class TestPerlMathOps:
    """Test Perl mathematical operations."""

    def test_integer_ops(self):
        assert perlthon.eval("2 + 3") == 5
        assert perlthon.eval("10 - 7") == 3
        assert perlthon.eval("6 * 7") == 42
        assert perlthon.eval("int(15 / 4)") == 3
        assert perlthon.eval("15 % 4") == 3

    def test_power(self):
        assert perlthon.eval("2 ** 16") == 65536

    def test_sqrt(self):
        result = perlthon.eval("sqrt(2)")
        assert abs(result - 1.41421356) < 1e-6

    def test_abs(self):
        assert perlthon.eval("abs(-99)") == 99
        result = perlthon.eval("abs(-3.14)")
        assert abs(result - 3.14) < 1e-10

    def test_sin_cos(self):
        result = perlthon.eval("sin(0)")
        assert abs(result) < 1e-10
        result = perlthon.eval("cos(0)")
        assert abs(result - 1.0) < 1e-10

    def test_atan2(self):
        import math

        result = perlthon.eval("atan2(1, 1)")
        assert abs(result - math.pi / 4) < 1e-10

    def test_log_exp(self):
        result = perlthon.eval("log(1)")
        assert abs(result) < 1e-10
        result = perlthon.eval("exp(0)")
        assert abs(result - 1.0) < 1e-10

    def test_rand_range(self):
        # rand returns [0, 1)
        for _ in range(10):
            result = perlthon.eval("rand()")
            assert 0 <= result < 1

    def test_bitwise_ops(self):
        assert perlthon.eval("0xFF & 0x0F") == 15
        assert perlthon.eval("0xF0 | 0x0F") == 255
        assert perlthon.eval("0xFF ^ 0x0F") == 240
        assert perlthon.eval("~0 & 0xFF") == 255
        assert perlthon.eval("1 << 8") == 256
        assert perlthon.eval("256 >> 4") == 16

    def test_increment_decrement(self):
        assert perlthon.eval("do { my $x = 5; ++$x }") == 6
        assert perlthon.eval("do { my $x = 5; --$x }") == 4

    def test_compound_assignment(self):
        assert perlthon.eval("do { my $x = 10; $x += 5; $x }") == 15
        assert perlthon.eval("do { my $x = 10; $x -= 3; $x }") == 7
        assert perlthon.eval("do { my $x = 10; $x *= 2; $x }") == 20
        assert perlthon.eval("do { my $x = 10; $x /= 4; $x }") == 2.5


class TestPerlFileOps:
    """Test Perl file operation functions (non-destructive)."""

    def test_file_test_exists(self):
        # /tmp should always exist
        assert perlthon.eval('-e "/tmp" ? 1 : 0') == 1

    def test_file_test_directory(self):
        assert perlthon.eval('-d "/tmp" ? 1 : 0') == 1

    def test_file_test_not_exists(self):
        assert perlthon.eval('-e "/nonexistent_xyz_123" ? 1 : 0') == 0

    def test_file_spec_splitpath(self):
        perlthon.use("File::Spec")
        result = perlthon.eval("""
            do {
                my ($vol, $dir, $file) = File::Spec->splitpath("/usr/local/bin/perl");
                [$vol, $dir, $file]
            }
        """)
        assert result[2] == "perl"

    def test_file_spec_catdir(self):
        perlthon.use("File::Spec")
        result = perlthon.eval('File::Spec->catdir("/usr", "local", "lib")')
        assert result == "/usr/local/lib"

    def test_file_spec_rel2abs(self):
        perlthon.use("File::Spec")
        result = perlthon.eval('File::Spec->rel2abs(".")')
        assert isinstance(result, str)
        assert result.startswith("/")

    def test_cwd_getcwd(self):
        perlthon.use("Cwd")
        result = perlthon.call("Cwd::getcwd")
        assert isinstance(result, str)
        assert "/" in result


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

    def test_very_long_eval(self):
        # Build a very long expression
        code = " + ".join(["1"] * 1000)
        assert perlthon.eval(code) == 1000

    def test_many_array_elements(self):
        result = perlthon.eval("[1..5000]")
        assert len(result) == 5000

    def test_hash_with_special_chars_in_keys(self):
        result = perlthon.eval('{"key with spaces" => 1, "key-with-dashes" => 2}')
        assert result["key with spaces"] == 1
        assert result["key-with-dashes"] == 2

    def test_empty_hash_value(self):
        result = perlthon.eval('{"key" => ""}')
        assert result == {"key": ""}

    def test_mixed_nesting_depth(self):
        result = perlthon.eval("""
            {
                "flat" => 1,
                "nested" => {"a" => [1, 2]},
                "deep" => {"x" => {"y" => {"z" => 99}}}
            }
        """)
        assert result["flat"] == 1
        assert result["nested"]["a"] == [1, 2]
        assert result["deep"]["x"]["y"]["z"] == 99

    def test_sequential_evals_share_state(self):
        perlthon.eval("$main::shared_var = 42")
        result = perlthon.eval("$main::shared_var")
        assert result == 42

    def test_eval_returns_last_expression(self):
        result = perlthon.eval("1; 2; 3; 4; 5")
        assert result == 5

    def test_multiline_eval(self):
        code = """
        my @nums = (1..10);
        my @evens = grep { $_ % 2 == 0 } @nums;
        my $sum = 0;
        $sum += $_ for @evens;
        $sum
        """
        assert perlthon.eval(code) == 30

    def test_eval_with_semicolons(self):
        result = perlthon.eval("my $x = 1; my $y = 2; my $z = 3; $x + $y + $z")
        assert result == 6

    def test_hundred_rapid_evals(self):
        results = [perlthon.eval(f"{i} * 2") for i in range(100)]
        assert results == [i * 2 for i in range(100)]

    def test_alternating_eval_and_call(self):
        perlthon.use("POSIX")
        for i in range(20):
            assert perlthon.eval(f"{i} + 0.5") == i + 0.5
            assert perlthon.call("POSIX::floor", i + 0.5) == float(i)


class TestPerlBuiltins:
    """Test various Perl built-in functions."""

    def test_defined(self):
        assert perlthon.eval("defined(42) ? 1 : 0") == 1
        assert perlthon.eval("defined(undef) ? 1 : 0") == 0

    def test_ref(self):
        assert perlthon.eval('ref([]) eq "ARRAY" ? 1 : 0') == 1
        assert perlthon.eval('ref({}) eq "HASH" ? 1 : 0') == 1

    def test_scalar(self):
        assert perlthon.eval("scalar @{[1,2,3,4,5]}") == 5

    def test_wantarray(self):
        # In scalar context eval, wantarray returns false
        result = perlthon.eval("wantarray() ? 1 : 0")
        assert result == 0

    def test_die_eval_catch(self):
        result = perlthon.eval("""
            do {
                my $error;
                eval { die "oops\\n" };
                $error = $@;
                chomp $error;
                $error
            }
        """)
        assert result == "oops"

    def test_local_time(self):
        result = perlthon.eval("do { my @t = localtime(0); $t[5] + 1900 }")
        assert result == 1970

    def test_time_returns_integer(self):
        result = perlthon.eval("time()")
        assert isinstance(result, int)
        assert result > 0

    def test_exists_in_hash(self):
        code = "do { my %h = (a => 1, b => 2); exists $h{a} ? 1 : 0 }"
        assert perlthon.eval(code) == 1
        code = "do { my %h = (a => 1, b => 2); exists $h{c} ? 1 : 0 }"
        assert perlthon.eval(code) == 0

    def test_delete_from_hash(self):
        code = "do { my %h = (a => 1, b => 2, c => 3); delete $h{b}; scalar keys %h }"
        assert perlthon.eval(code) == 2

    def test_push_pop(self):
        code = "do { my @a = (1,2,3); push @a, 4; pop @a }"
        assert perlthon.eval(code) == 4

    def test_shift_unshift(self):
        code = "do { my @a = (1,2,3); unshift @a, 0; shift @a }"
        assert perlthon.eval(code) == 0

    def test_chomp_returns_count(self):
        result = perlthon.eval('do { my $s = "hi\\n"; chomp $s }')
        assert result == 1

    def test_hex_function(self):
        assert perlthon.eval('hex("ff")') == 255
        assert perlthon.eval('hex("0x1A")') == 26

    def test_oct_function(self):
        assert perlthon.eval('oct("77")') == 63
        assert perlthon.eval('oct("0b1111")') == 15

    def test_lc_uc(self):
        assert perlthon.eval('lc("FOO BAR")') == "foo bar"
        assert perlthon.eval('uc("foo bar")') == "FOO BAR"

    def test_sprintf_padding(self):
        assert perlthon.eval('sprintf("%10s", "hi")') == "        hi"
        assert perlthon.eval('sprintf("%-10s", "hi")') == "hi        "

    def test_join_with_separator(self):
        result = perlthon.eval('join(":", "a", "b", "c", "d")')
        assert result == "a:b:c:d"

    def test_split_limit(self):
        result = perlthon.eval('[split(/,/, "a,b,c,d,e", 3)]')
        assert result == ["a", "b", "c,d,e"]

    def test_sort_numeric(self):
        result = perlthon.eval("[sort { $a <=> $b } (10, 2, 30, 4, 50)]")
        assert result == [2, 4, 10, 30, 50]

    def test_sort_reverse(self):
        result = perlthon.eval("[sort { $b <=> $a } (1, 2, 3, 4, 5)]")
        assert result == [5, 4, 3, 2, 1]

    def test_map_transform(self):
        result = perlthon.eval("[map { $_ * $_ } (1, 2, 3, 4, 5)]")
        assert result == [1, 4, 9, 16, 25]

    def test_grep_pattern(self):
        result = perlthon.eval(
            '[grep { /^a/ } ("apple", "banana", "avocado", "cherry")]'
        )
        assert result == ["apple", "avocado"]
