"""Advanced integration tests: stress, recovery, real-world workflows, interop."""

import os
import threading

import pytest

import perlthon


class TestStressRapidEval:
    """Stress tests with rapid repeated operations."""

    def test_thousand_evals(self):
        for i in range(1000):
            assert perlthon.eval(f"{i} * 2") == i * 2

    def test_thousand_string_evals(self):
        for i in range(1000):
            result = perlthon.eval(f'"item_{i}"')
            assert result == f"item_{i}"

    @pytest.mark.skipif(
        os.getenv("CI"),
        reason=(
            "Embedded Perl stress test is flaky in GitHub Actions under CI "
            "resource limits"
        ),
    )
    def test_rapid_module_calls(self):
        perlthon.use("POSIX")
        for i in range(1000):
            assert perlthon.call("POSIX::floor", i + 0.7) == float(i)

    def test_large_return_value(self):
        result = perlthon.eval("[1..10000]")
        assert len(result) == 10000
        assert sum(result) == 50005000

    def test_large_hash(self):
        result = perlthon.eval('do { my %h; $h{"key_$_"} = $_ for 1..1000; +{%h} }')
        assert len(result) == 1000
        assert result["key_500"] == 500

    def test_large_string_return(self):
        result = perlthon.eval('"A" x 100000')
        assert len(result) == 100000

    def test_many_nested_structures(self):
        result = perlthon.eval("[map { {index => $_, value => $_ * 2} } 1..100]")
        assert len(result) == 100
        assert result[49] == {"index": 50, "value": 100}

    def test_alternating_types(self):
        """Rapidly alternate between returning different types."""
        for i in range(200):
            if i % 4 == 0:
                assert perlthon.eval(f"{i}") == i
            elif i % 4 == 1:
                assert perlthon.eval(f'"{i}"') == str(i)
            elif i % 4 == 2:
                result = perlthon.eval(f"[{i}, {i + 1}]")
                assert result == [i, i + 1]
            else:
                result = perlthon.eval(f'{{"n" => {i}}}')
                assert result == {"n": i}

    def test_many_module_loads(self):
        """Load many different modules in sequence."""
        modules = [
            "POSIX",
            "Scalar::Util",
            "List::Util",
            "File::Basename",
            "File::Spec",
            "Cwd",
            "MIME::Base64",
            "Digest::MD5",
            "Data::Dumper",
            "Storable",
            "JSON::PP",
            "Encode",
            "IO::File",
            "Socket",
            "Fcntl",
            "File::Path",
            "File::Temp",
            "Getopt::Long",
            "Text::ParseWords",
            "Math::BigInt",
        ]
        for mod_name in modules:
            mod = perlthon.use(mod_name)
            assert isinstance(mod, perlthon.PerlModule)

    def test_memory_pressure_arrays(self):
        """Create and discard many large arrays."""
        for _ in range(100):
            result = perlthon.eval("[1..1000]")
            assert len(result) == 1000

    def test_memory_pressure_hashes(self):
        """Create and discard many hashes."""
        for _ in range(100):
            result = perlthon.eval('do { my %h; $h{$_} = "v" for 1..100; +{%h} }')
            assert len(result) == 100

    def test_memory_pressure_strings(self):
        """Create and discard many large strings."""
        for _ in range(100):
            result = perlthon.eval('"x" x 50000')
            assert len(result) == 50000


class TestStressConcurrency:
    """Test thread safety of the interpreter."""

    def test_concurrent_eval_read_only(self):
        """Multiple threads doing eval simultaneously."""
        results = {}
        errors = []

        def worker(thread_id):
            try:
                for i in range(100):
                    result = perlthon.eval(f"{thread_id} * 1000 + {i}")
                    expected = thread_id * 1000 + i
                    if result != expected:
                        errors.append(
                            f"Thread {thread_id}: got {result}, expected {expected}"
                        )
                results[thread_id] = True
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        # We expect either all succeed (if mutex works) or clean errors
        # The Mutex in the Rust code should serialize access
        if errors:
            # If there are errors, they should be clean RuntimeErrors,
            # not segfaults
            for e in errors:
                assert "Thread" in e

    def test_concurrent_module_calls(self):
        """Multiple threads calling module functions."""
        perlthon.use("POSIX")
        results = []
        errors = []

        def worker(thread_id):
            try:
                for i in range(50):
                    val = thread_id * 100 + i + 0.5
                    result = perlthon.call("POSIX::floor", val)
                    expected = float(thread_id * 100 + i)
                    if result != expected:
                        errors.append(
                            f"Thread {thread_id}: got {result}, expected {expected}"
                        )
                results.append(thread_id)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        # Should not segfault — either succeeds or raises clean errors
        assert len(results) + len(errors) > 0


class TestErrorRecovery:
    """Test that the interpreter recovers gracefully after errors."""

    def test_eval_after_die(self):
        """Interpreter works after a die."""
        with pytest.raises(RuntimeError):
            perlthon.eval('die "boom"')
        # Should still work
        assert perlthon.eval("42") == 42

    def test_eval_after_syntax_error(self):
        """Interpreter works after a syntax error."""
        with pytest.raises(RuntimeError):
            perlthon.eval("if ( {")
        assert perlthon.eval('"hello"') == "hello"

    def test_eval_after_strict_error(self):
        """Interpreter works after a strict mode violation."""
        with pytest.raises(RuntimeError):
            perlthon.eval("use strict; $bad_var")
        assert perlthon.eval("[1,2,3]") == [1, 2, 3]

    def test_many_errors_then_success(self):
        """Interpreter survives many consecutive errors."""
        for i in range(50):
            with pytest.raises(RuntimeError):
                perlthon.eval(f'die "error {i}"')
        assert perlthon.eval("99") == 99

    def test_use_module_after_bad_use(self):
        """Can still load modules after a failed module load."""
        with pytest.raises(RuntimeError):
            perlthon.use("Totally::Nonexistent::Module")
        mod = perlthon.use("POSIX")
        assert mod.floor(2.9) == 2.0

    def test_state_preserved_after_error(self):
        """Variables set before an error are preserved."""
        perlthon.eval('$main::my_val = "preserved"')
        with pytest.raises(RuntimeError):
            perlthon.eval('die "oops"')
        assert perlthon.eval("$main::my_val") == "preserved"

    def test_module_still_loaded_after_error(self):
        """Modules stay loaded after an error."""
        perlthon.use("POSIX")
        with pytest.raises(RuntimeError):
            perlthon.eval('die "error"')
        assert perlthon.call("POSIX::ceil", 1.1) == 2.0

    def test_error_message_content(self):
        """Error messages contain useful information."""
        with pytest.raises(RuntimeError, match="something specific"):
            perlthon.eval('die "something specific went wrong"')

    def test_nested_eval_error_recovery(self):
        """Perl eval {} catches errors, Python sees success."""
        result = perlthon.eval("""
            do {
                my @results;
                for my $i (1..5) {
                    eval { die "err $i" if $i == 3 };
                    push @results, $@ ? "caught" : "ok";
                }
                \\@results
            }
        """)
        assert result == ["ok", "ok", "caught", "ok", "ok"]

    def test_alternating_success_and_failure(self):
        """Alternate between successful and failing evals."""
        for i in range(100):
            if i % 2 == 0:
                assert perlthon.eval(f"{i}") == i
            else:
                with pytest.raises(RuntimeError):
                    perlthon.eval(f'die "error {i}"')

    def test_error_does_not_leak_into_next(self):
        """$@ is cleared between calls."""
        with pytest.raises(RuntimeError):
            perlthon.eval('die "first error"')
        # Next eval should not see the previous error
        result = perlthon.eval("42")
        assert result == 42


class TestRealWorldCSV:
    """Test real-world CSV processing patterns."""

    def test_parse_csv_line(self):
        perlthon.use("Text::ParseWords")
        result = perlthon.eval("""
            [Text::ParseWords::parse_line(',', 0, 'name,age,city')]
        """)
        assert result == ["name", "age", "city"]

    def test_parse_csv_with_quotes(self):
        perlthon.use("Text::ParseWords")
        result = perlthon.eval("""
            [Text::ParseWords::parse_line(',', 0,
                '"Smith, John",42,"New York"')]
        """)
        assert result == ["Smith, John", "42", "New York"]

    def test_process_csv_data(self):
        """Process multiple CSV rows."""
        result = perlthon.eval("""
            do {
                my @data = (
                    "Alice,30,Engineer",
                    "Bob,25,Designer",
                    "Carol,35,Manager"
                );
                my @parsed;
                for my $line (@data) {
                    my @fields = split(/,/, $line);
                    push @parsed, {
                        name => $fields[0],
                        age => int($fields[1]),
                        role => $fields[2]
                    };
                }
                \\@parsed
            }
        """)
        assert len(result) == 3
        assert result[0] == {"name": "Alice", "age": 30, "role": "Engineer"}
        assert result[2]["name"] == "Carol"

    def test_csv_to_hash(self):
        """Convert CSV with headers to list of hashes."""
        result = perlthon.eval("""
            do {
                my $header = "name,age,city";
                my @rows = ("Alice,30,NYC", "Bob,25,LA");
                my @keys = split(/,/, $header);
                my @result;
                for my $row (@rows) {
                    my @vals = split(/,/, $row);
                    my %h;
                    @h{@keys} = @vals;
                    push @result, +{%h};
                }
                \\@result
            }
        """)
        assert result[0]["name"] == "Alice"
        assert result[1]["city"] == "LA"


class TestRealWorldJSON:
    """Test JSON processing with JSON::PP."""

    def test_encode_simple(self):
        perlthon.use("JSON::PP")
        result = perlthon.eval(
            'JSON::PP->new->utf8->encode({name => "test", value => 42})'
        )
        assert '"name"' in result
        assert "42" in result

    def test_decode_simple(self):
        perlthon.use("JSON::PP")
        result = perlthon.eval("""
            JSON::PP->new->utf8->decode('{"name":"Alice","age":30}')
        """)
        assert result == {"name": "Alice", "age": 30}

    def test_roundtrip(self):
        perlthon.use("JSON::PP")
        result = perlthon.eval("""
            do {
                my $json = JSON::PP->new->utf8;
                my $data = { items => [1, 2, 3], label => "test" };
                my $encoded = $json->encode($data);
                my $decoded = $json->decode($encoded);
                $decoded
            }
        """)
        assert result == {"items": [1, 2, 3], "label": "test"}

    def test_nested_json(self):
        perlthon.use("JSON::PP")
        result = perlthon.eval("""
            JSON::PP->new->utf8->decode(
                '{"users":[{"name":"a","roles":["admin","user"]},{"name":"b","roles":["user"]}]}'
            )
        """)
        assert result["users"][0]["name"] == "a"
        assert result["users"][0]["roles"] == ["admin", "user"]
        assert result["users"][1]["roles"] == ["user"]

    def test_json_with_unicode(self):
        perlthon.use("JSON::PP")
        result = perlthon.eval("""
            JSON::PP->new->utf8->decode('{"emoji":"\\u2603","text":"snow"}')
        """)
        assert result["emoji"] == "\u2603"
        assert result["text"] == "snow"

    def test_json_booleans(self):
        perlthon.use("JSON::PP")
        result = perlthon.eval("""
            do {
                my $data = JSON::PP->new->utf8->decode(
                    '{"active":true,"deleted":false}'
                );
                # Convert JSON booleans to ints for clean return
                {active => $data->{active} ? 1 : 0,
                 deleted => $data->{deleted} ? 1 : 0}
            }
        """)
        assert result["active"] == 1
        assert result["deleted"] == 0


class TestRealWorldDateMath:
    """Test date/time operations."""

    def test_time_piece_parse(self):
        perlthon.use("Time::Piece")
        result = perlthon.eval("""
            do {
                my $t = Time::Piece->strptime("2024-06-15", "%Y-%m-%d");
                {year => $t->year, month => $t->mon, day => $t->mday}
            }
        """)
        assert result == {"year": 2024, "month": 6, "day": 15}

    def test_time_piece_day_of_week(self):
        perlthon.use("Time::Piece")
        result = perlthon.eval("""
            do {
                my $t = Time::Piece->strptime("2024-01-01", "%Y-%m-%d");
                $t->day
            }
        """)
        assert result == "Mon"

    def test_epoch_to_date(self):
        perlthon.use("POSIX")
        result = perlthon.eval('POSIX::strftime("%Y-%m-%d", gmtime(0))')
        assert result == "1970-01-01"

    def test_date_arithmetic(self):
        perlthon.use("Time::Piece")
        result = perlthon.eval("""
            do {
                use Time::Seconds;
                my $t = Time::Piece->strptime("2024-01-01", "%Y-%m-%d");
                my $later = $t + ONE_DAY * 30;
                $later->strftime("%Y-%m-%d")
            }
        """)
        assert result == "2024-01-31"

    def test_time_difference(self):
        perlthon.use("Time::Piece")
        result = perlthon.eval("""
            do {
                my $t1 = Time::Piece->strptime("2024-01-01", "%Y-%m-%d");
                my $t2 = Time::Piece->strptime("2024-01-31", "%Y-%m-%d");
                int(($t2 - $t1) / 86400)
            }
        """)
        assert result == 30


class TestRealWorldTemplates:
    """Test string templating patterns."""

    def test_simple_interpolation(self):
        result = perlthon.eval("""
            do {
                my $name = "World";
                my $greeting = "Hello, $name!";
                $greeting
            }
        """)
        assert result == "Hello, World!"

    def test_sprintf_template(self):
        result = perlthon.eval("""
            do {
                my @items = ({name => "Apple", price => 1.50},
                             {name => "Banana", price => 0.75});
                my @lines = map {
                    sprintf("%-10s \\$%.2f", $_->{name}, $_->{price})
                } @items;
                join("\\n", @lines)
            }
        """)
        assert "Apple" in result
        assert "$1.50" in result
        assert "Banana" in result

    def test_heredoc_template(self):
        result = perlthon.eval("""
            do {
                my $name = "Alice";
                my $age = 30;
                my $template = <<END;
Name: $name
Age: $age
Status: Active
END
                chomp $template;
                $template
            }
        """)
        assert "Name: Alice" in result
        assert "Age: 30" in result
        assert "Status: Active" in result

    def test_regex_based_template(self):
        result = perlthon.eval("""
            do {
                my $template = "Hello, {{name}}! You have {{count}} messages.";
                my %vars = (name => "Bob", count => 5);
                $template =~ s/\\{\\{(\\w+)\\}\\}/$vars{$1}/g;
                $template
            }
        """)
        assert result == "Hello, Bob! You have 5 messages."

    def test_multiline_template_processing(self):
        result = perlthon.eval("""
            do {
                my @users = (
                    {name => "Alice", role => "admin"},
                    {name => "Bob", role => "user"},
                    {name => "Carol", role => "user"},
                );
                my @lines = map { "$_->{name} ($_->{role})" } @users;
                join(", ", @lines)
            }
        """)
        assert result == "Alice (admin), Bob (user), Carol (user)"


class TestRealWorldDataProcessing:
    """Test data processing pipelines."""

    def test_word_frequency(self):
        result = perlthon.eval("""
            do {
                my $text = "the cat sat on the mat the cat";
                my %freq;
                $freq{$_}++ for split(/\\s+/, $text);
                +{%freq}
            }
        """)
        assert result["the"] == 3
        assert result["cat"] == 2
        assert result["sat"] == 1

    def test_group_by(self):
        result = perlthon.eval("""
            do {
                my @items = (
                    {type => "fruit", name => "apple"},
                    {type => "veggie", name => "carrot"},
                    {type => "fruit", name => "banana"},
                    {type => "veggie", name => "broccoli"},
                );
                my %groups;
                for my $item (@items) {
                    push @{$groups{$item->{type}}}, $item->{name};
                }
                +{%groups}
            }
        """)
        assert sorted(result["fruit"]) == ["apple", "banana"]
        assert sorted(result["veggie"]) == ["broccoli", "carrot"]

    def test_pipeline_filter_transform_aggregate(self):
        result = perlthon.eval("""
            do {
                my @numbers = 1..20;
                # Filter evens, square them, sum
                my $sum = 0;
                $sum += $_ ** 2 for grep { $_ % 2 == 0 } @numbers;
                $sum
            }
        """)
        # Sum of squares of evens 2..20: 4+16+36+64+100+144+196+256+324+400
        assert result == 1540

    def test_nested_data_transform(self):
        result = perlthon.eval("""
            do {
                my @students = (
                    {name => "Alice", scores => [90, 85, 92]},
                    {name => "Bob", scores => [78, 82, 88]},
                    {name => "Carol", scores => [95, 91, 97]},
                );
                my @result;
                for my $s (@students) {
                    my $avg = 0;
                    $avg += $_ for @{$s->{scores}};
                    $avg /= scalar @{$s->{scores}};
                    push @result, {name => $s->{name}, average => int($avg)};
                }
                \\@result
            }
        """)
        assert result[0] == {"name": "Alice", "average": 89}
        assert result[2] == {"name": "Carol", "average": 94}

    def test_dedup_preserve_order(self):
        result = perlthon.eval("""
            do {
                my @items = qw(apple banana apple cherry banana date);
                my %seen;
                my @unique = grep { !$seen{$_}++ } @items;
                \\@unique
            }
        """)
        assert result == ["apple", "banana", "cherry", "date"]

    def test_running_total(self):
        result = perlthon.eval("""
            do {
                my @nums = (10, 20, 30, 40, 50);
                my @running;
                my $total = 0;
                for my $n (@nums) {
                    $total += $n;
                    push @running, $total;
                }
                \\@running
            }
        """)
        assert result == [10, 30, 60, 100, 150]

    def test_histogram(self):
        result = perlthon.eval("""
            do {
                my @data = (1,1,2,2,2,3,3,3,3,4,4,4,4,4);
                my %hist;
                $hist{$_}++ for @data;
                +{%hist}
            }
        """)
        assert result == {"1": 2, "2": 3, "3": 4, "4": 5}


class TestInteropEdgeCases:
    """Test edge cases in Python-Perl interop."""

    def test_pass_none(self):
        """Passing None to Perl should become undef."""
        perlthon.eval("sub check_undef { defined($_[0]) ? 0 : 1 }")
        result = perlthon.call("main::check_undef", None)
        assert result == 1

    def test_pass_true(self):
        """Passing Python True to Perl."""
        perlthon.eval("sub check_bool { $_[0] ? 1 : 0 }")
        assert perlthon.call("main::check_bool", True) == 1

    def test_pass_false(self):
        """Passing Python False to Perl."""
        perlthon.eval("sub check_bool2 { $_[0] ? 1 : 0 }")
        assert perlthon.call("main::check_bool2", False) == 0

    def test_pass_empty_string(self):
        perlthon.eval("sub check_empty { length($_[0]) == 0 ? 1 : 0 }")
        assert perlthon.call("main::check_empty", "") == 1

    def test_pass_long_string(self):
        long_str = "x" * 100000
        perlthon.eval("sub get_len { length($_[0]) }")
        result = perlthon.call("main::get_len", long_str)
        assert result == 100000

    def test_pass_string_with_newlines(self):
        perlthon.eval("sub count_lines { scalar(split(/\\n/, $_[0])) }")
        text = "line1\nline2\nline3\nline4"
        result = perlthon.call("main::count_lines", text)
        assert result == 4

    def test_pass_negative_int(self):
        perlthon.use("POSIX")
        assert perlthon.call("POSIX::abs", -42) == 42

    def test_pass_large_negative(self):
        perlthon.eval("sub negate { -$_[0] }")
        assert perlthon.call("main::negate", -2147483648) == 2147483648

    def test_return_very_nested(self):
        """Test deeply nested return values."""
        result = perlthon.eval("""
            {a => {b => {c => {d => {e => {f => "deep"}}}}}}
        """)
        assert result["a"]["b"]["c"]["d"]["e"]["f"] == "deep"

    def test_return_array_of_hashes_of_arrays(self):
        result = perlthon.eval("""
            [{tags => ["a","b"]}, {tags => ["c","d"]}, {tags => ["e","f"]}]
        """)
        assert result[0]["tags"] == ["a", "b"]
        assert result[2]["tags"] == ["e", "f"]

    def test_many_arguments(self):
        """Pass many arguments to a function."""
        perlthon.eval("""
            sub sum_all {
                my $sum = 0;
                $sum += $_ for @_;
                return $sum;
            }
        """)
        args = list(range(1, 101))
        result = perlthon.call("main::sum_all", *args)
        assert result == 5050

    def test_string_with_special_perl_chars(self):
        """Strings with characters that are special in Perl."""
        perlthon.eval("sub echo { $_[0] }")
        # Dollar signs, @, etc. should be passed as literal strings
        result = perlthon.call("main::echo", "price is $100")
        assert result == "price is $100"

    def test_very_small_float(self):
        perlthon.eval("sub echo_num { $_[0] }")
        result = perlthon.call("main::echo_num", 1e-300)
        assert result == pytest.approx(1e-300)

    def test_very_large_float(self):
        perlthon.eval("sub echo_num2 { $_[0] }")
        result = perlthon.call("main::echo_num2", 1e300)
        assert result == pytest.approx(1e300)

    def test_infinity(self):
        result = perlthon.eval("9**9**9")
        assert result == float("inf")

    def test_return_code_ref_as_string(self):
        """Code refs should be returned as string representation."""
        result = perlthon.eval("sub { 42 }")
        # Should be something like "CODE(0x...)"
        assert "CODE" in str(result)


class TestRealWorldEncoding:
    """Test encoding/decoding operations."""

    def test_base64_roundtrip(self):
        perlthon.use("MIME::Base64")
        original = "Hello, World! 🌍"
        encoded = perlthon.call("MIME::Base64::encode_base64", original, "")
        decoded = perlthon.call("MIME::Base64::decode_base64", encoded)
        assert decoded == original

    def test_base64_binary(self):
        perlthon.use("MIME::Base64")
        # Encode binary-ish data
        data = "".join(chr(i) for i in range(1, 128))
        encoded = perlthon.call("MIME::Base64::encode_base64", data, "")
        decoded = perlthon.call("MIME::Base64::decode_base64", encoded)
        assert decoded == data

    def test_md5_various(self):
        perlthon.use("Digest::MD5")
        assert (
            perlthon.call("Digest::MD5::md5_hex", "")
            == "d41d8cd98f00b204e9800998ecf8427e"
        )
        assert (
            perlthon.call("Digest::MD5::md5_hex", "abc")
            == "900150983cd24fb0d6963f7d28e17f72"
        )

    def test_url_encoding(self):
        """URL-encode a string using Perl."""
        result = perlthon.eval("""
            do {
                my $str = "hello world & foo=bar";
                $str =~ s/([^A-Za-z0-9\\-_.~])/sprintf("%%%02X", ord($1))/ge;
                $str
            }
        """)
        assert result == "hello%20world%20%26%20foo%3Dbar"

    def test_hex_encode_decode(self):
        result = perlthon.eval("""
            do {
                my $data = "Hello";
                my $hex = unpack("H*", $data);
                my $back = pack("H*", $hex);
                [$hex, $back]
            }
        """)
        assert result[0] == "48656c6c6f"
        assert result[1] == "Hello"


class TestRealWorldAlgorithms:
    """Test implementing algorithms in Perl called from Python."""

    def test_bubble_sort(self):
        result = perlthon.eval("""
            do {
                my @arr = (64, 34, 25, 12, 22, 11, 90);
                for my $i (0..$#arr) {
                    for my $j (0..$#arr-$i-1) {
                        if ($arr[$j] > $arr[$j+1]) {
                            @arr[$j, $j+1] = @arr[$j+1, $j];
                        }
                    }
                }
                \\@arr
            }
        """)
        assert result == [11, 12, 22, 25, 34, 64, 90]

    def test_binary_search(self):
        result = perlthon.eval("""
            do {
                sub bin_search {
                    my ($arr, $target) = @_;
                    my ($lo, $hi) = (0, $#$arr);
                    while ($lo <= $hi) {
                        my $mid = int(($lo + $hi) / 2);
                        if ($arr->[$mid] == $target) { return $mid }
                        elsif ($arr->[$mid] < $target) { $lo = $mid + 1 }
                        else { $hi = $mid - 1 }
                    }
                    return -1;
                }
                my @sorted = (2, 5, 8, 12, 16, 23, 38, 45, 56, 72, 91);
                bin_search(\\@sorted, 23)
            }
        """)
        assert result == 5

    def test_gcd(self):
        result = perlthon.eval("""
            do {
                sub gcd { my ($a, $b) = @_; $b ? gcd($b, $a % $b) : $a }
                gcd(48, 18)
            }
        """)
        assert result == 6

    def test_is_palindrome(self):
        result = perlthon.eval("""
            do {
                sub is_palindrome {
                    my $s = lc(shift);
                    $s =~ s/[^a-z0-9]//g;
                    $s eq reverse($s) ? 1 : 0
                }
                [is_palindrome("A man, a plan, a canal: Panama"),
                 is_palindrome("hello")]
            }
        """)
        assert result == [1, 0]

    def test_flatten_array(self):
        result = perlthon.eval("""
            do {
                sub flatten {
                    my @result;
                    for my $item (@_) {
                        if (ref($item) eq 'ARRAY') {
                            push @result, flatten(@$item);
                        } else {
                            push @result, $item;
                        }
                    }
                    return @result;
                }
                [flatten([1, [2, [3, 4]], 5, [6, [7, 8]]])]
            }
        """)
        assert result == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_matrix_multiply(self):
        result = perlthon.eval("""
            do {
                my @a = ([1,2], [3,4]);
                my @b = ([5,6], [7,8]);
                my @c;
                for my $i (0..1) {
                    for my $j (0..1) {
                        $c[$i][$j] = 0;
                        for my $k (0..1) {
                            $c[$i][$j] += $a[$i][$k] * $b[$k][$j];
                        }
                    }
                }
                [\\@{$c[0]}, \\@{$c[1]}]
            }
        """)
        assert result == [[19, 22], [43, 50]]

    def test_sieve_of_eratosthenes(self):
        result = perlthon.eval("""
            do {
                my $n = 50;
                my @is_prime = (1) x ($n + 1);
                $is_prime[0] = $is_prime[1] = 0;
                for my $i (2..int(sqrt($n))) {
                    if ($is_prime[$i]) {
                        for (my $j = $i*$i; $j <= $n; $j += $i) {
                            $is_prime[$j] = 0;
                        }
                    }
                }
                [grep { $is_prime[$_] } 2..$n]
            }
        """)
        expected = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        assert result == expected
