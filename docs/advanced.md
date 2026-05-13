# Advanced Usage

Advanced patterns, recipes, and best practices for Perlthon.

## Complex Eval Patterns

### Multi-statement evaluation

```python
import perlthon

# Use do-blocks for complex logic
result = perlthon.eval("""
do {
    my @nums = (1..10);
    my @evens = grep { $_ % 2 == 0 } @nums;
    [map { $_ ** 2 } @evens]
}
""")
# → [4, 16, 36, 64, 100]
```

### Regular expressions

```python
import perlthon

# Extract matches
match = perlthon.eval('''
do {
    "2025-01-15" =~ /(\d{4})-(\d{2})-(\d{2})/;
    [$1, $2, $3]
}
''')
# → ["2025", "01", "15"]

# Global substitution
cleaned = perlthon.eval('''
do {
    my $s = "  too   many   spaces  ";
    $s =~ s/\s+/ /g;
    $s =~ s/^\s+|\s+$//g;
    $s
}
''')
# → "too many spaces"
```

### Building data pipelines

```python
import perlthon

# Process text with Perl's strengths
result = perlthon.eval('''
do {
    my @lines = split /\\n/, "name:alice\\nage:30\\ncity:london";
    my %data = map { split /:/, $_, 2 } @lines;
    +{%data}
}
''')
# → {"name": "alice", "age": "30", "city": "london"}
```

## Performance Tips

### Batch operations in eval

Instead of calling `eval` in a loop, batch work into a single Perl expression:

```python
import perlthon

# ❌ Slow: many cross-language calls
results = [perlthon.eval(f"sqrt({x})") for x in range(1000)]

# ✅ Fast: single call, process in Perl
results = perlthon.eval("[map { sqrt($_) } (0..999)]")
```

### Reuse module references

```python
import perlthon

# Module loading is cached internally, but keeping a reference is clearer
posix = perlthon.use("POSIX")

# All calls go through the same interpreter
for value in large_dataset:
    processed = posix.floor(value)
```

## Interoperability Patterns

### Using Perl for text processing, Python for everything else

```python
import perlthon

def perl_extract_emails(text: str) -> list[str]:
    """Use Perl's regex engine to extract emails."""
    # Escape the text for safe embedding
    escaped = text.replace("\\", "\\\\").replace("'", "\\'")
    return perlthon.eval(f"""
    do {{
        my $text = '{escaped}';
        my @emails = ($text =~ /[\\w.+-]+\\@[\\w.-]+\\.\\w+/g);
        \\@emails
    }}
    """)

emails = perl_extract_emails("Contact alice@example.com or bob@test.org")
# → ["alice@example.com", "bob@test.org"]
```

### Wrapping Perl modules in Python classes

```python
import perlthon


class PerlJSON:
    """Python wrapper around Perl's JSON module."""

    def __init__(self):
        self._mod = perlthon.use("JSON::PP")

    def encode(self, data: dict | list) -> str:
        # Convert Python structure via eval
        return perlthon.eval(f"JSON::PP::encode_json({_to_perl(data)})")

    def decode(self, json_str: str) -> dict | list:
        escaped = json_str.replace("\\", "\\\\").replace("'", "\\'")
        return perlthon.eval(f"JSON::PP::decode_json('{escaped}')")
```

## Error Handling Patterns

### Catching specific Perl errors

```python
import perlthon

def safe_eval(code: str, default=None):
    """Evaluate Perl code, returning a default on error."""
    try:
        return perlthon.eval(code)
    except RuntimeError as e:
        if "Can't locate" in str(e):
            raise ModuleNotFoundError(str(e)) from e
        return default
```

### Validating input before sending to Perl

```python
import perlthon

def safe_call(module: str, func: str, *args):
    """Call a Perl function with type checking."""
    for arg in args:
        if not isinstance(arg, (int, float, str, bool, type(None))):
            raise TypeError(f"Cannot pass {type(arg).__name__} to Perl")
    perlthon.use(module)
    return perlthon.call(f"{module}::{func}", *args)
```

## The Interpreter Lifecycle

Perlthon uses a singleton Perl interpreter that is created on first use and
lives for the duration of the Python process. This means:

- Module loads persist across calls (no re-loading overhead)
- Global Perl state is shared across all `eval`/`call`/`use` invocations
- The interpreter is thread-safe at the Python level (GIL protected)

```python
import perlthon

# First call creates the interpreter
perlthon.eval("1")

# Subsequent calls reuse it — modules stay loaded
perlthon.use("POSIX")
perlthon.use("List::Util")

# Both modules are available for the rest of the process
```
