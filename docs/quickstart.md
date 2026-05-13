# Quick Start

Get up and running with Perlthon in minutes.

## Installation

```bash
# From source (requires Rust toolchain + Perl dev headers)
pip install .

# For development
uv sync
```

## Your First Perlthon Script

```python
import perlthon

# Evaluate arbitrary Perl expressions
result = perlthon.eval('42 * 2')
print(result)  # 84

# String operations
greeting = perlthon.eval('"Hello, " . "World!"')
print(greeting)  # Hello, World!
```

## Using Perl Modules

```python
import perlthon

# Load a Perl module (like Perl's `use`)
posix = perlthon.use("POSIX")

# Call methods on the module
print(posix.floor(3.7))  # 3.0
print(posix.ceil(3.2))   # 4.0

# Use File::Basename
fb = perlthon.use("File::Basename")
print(fb.basename("/usr/local/bin/perl"))  # perl
print(fb.dirname("/usr/local/bin/perl"))   # /usr/local/bin
```

## Calling Functions Directly

```python
import perlthon

# Load the module first
perlthon.use("POSIX")

# Call by fully qualified name
result = perlthon.call("POSIX::floor", 9.9)
print(result)  # 9.0
```

## Working with Data Structures

Perl data structures are automatically converted to Python equivalents:

```python
import perlthon

# Array references become Python lists
nums = perlthon.eval("[1, 2, 3, 4, 5]")
print(nums)  # [1, 2, 3, 4, 5]

# Hash references become Python dicts
data = perlthon.eval('{"name" => "perl", "version" => 5}')
print(data)  # {'name': 'perl', 'version': 5}

# Nested structures work too
nested = perlthon.eval('{"users" => [{"name" => "Alice"}, {"name" => "Bob"}]}')
print(nested["users"][0]["name"])  # Alice
```

## Error Handling

Perl errors are raised as Python `RuntimeError` exceptions:

```python
import perlthon

try:
    perlthon.eval('die "something went wrong"')
except RuntimeError as e:
    print(f"Perl error: {e}")

try:
    perlthon.use("Nonexistent::Module")
except RuntimeError as e:
    print(f"Module not found: {e}")
```

## Next Steps

- {doc}`api` — Full API reference
- {doc}`modules` — Tips for working with Perl modules
- {doc}`advanced` — Advanced patterns and recipes
