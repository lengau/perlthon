import pytest

import perlthon


RECURSION_ERROR = "Maximum recursion depth exceeded"


def _nested_list(depth: int) -> list[object]:
    root: list[object] = []
    current = root
    for _ in range(depth):
        child: list[object] = []
        current.append(child)
        current = child
    return root


class TestPythonToPerlRecursion:
    def setup_method(self):
        perlthon.eval("sub consume { return undef }")

    def test_recursive_list_argument_raises_runtime_error(self):
        value: list[object] = []
        value.append(value)

        with pytest.raises(RuntimeError, match=RECURSION_ERROR):
            perlthon.call("main::consume", value)

    def test_recursive_dict_argument_raises_runtime_error(self):
        value: dict[str, object] = {}
        value["self"] = value

        with pytest.raises(RuntimeError, match=RECURSION_ERROR):
            perlthon.call("main::consume", value)

    def test_deeply_nested_list_argument_raises_runtime_error(self):
        value = _nested_list(101)

        with pytest.raises(RuntimeError, match=RECURSION_ERROR):
            perlthon.call("main::consume", value)


class TestPerlToPythonRecursion:
    def test_recursive_array_result_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match=RECURSION_ERROR):
            perlthon.eval("do { my $a = []; push @$a, $a; $a }")

    def test_recursive_hash_result_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match=RECURSION_ERROR):
            perlthon.eval("do { my $h = {}; $h->{self} = $h; $h }")

    def test_deeply_nested_array_result_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match=RECURSION_ERROR):
            perlthon.eval(
                "do { my $value = 1; for (1..101) { $value = [$value] } $value }"
            )
