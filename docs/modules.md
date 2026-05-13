# Working with Perl Modules

Tips and patterns for using Perl modules from Python.

## Core Modules

These modules ship with Perl and are always available:

### POSIX

Mathematical and system functions from the C standard library.

```python
import perlthon

posix = perlthon.use("POSIX")

posix.floor(3.7)    # → 3.0
posix.ceil(3.2)     # → 4.0
posix.pow(2, 10)    # → 1024.0
posix.sqrt(144)     # → 12.0
posix.fmod(10, 3)   # → 1.0
```

### File::Basename

Parse file paths.

```python
fb = perlthon.use("File::Basename")

fb.basename("/usr/local/bin/perl")          # → "perl"
fb.dirname("/usr/local/bin/perl")           # → "/usr/local/bin"
fb.fileparse("/home/user/doc.txt", ".txt")  # → "doc"
```

### List::Util

Utility functions for lists.

```python
lu = perlthon.use("List::Util")

lu.sum(1, 2, 3, 4, 5)    # → 15
lu.min(5, 2, 8, 1, 9)    # → 1
lu.max(5, 2, 8, 1, 9)    # → 9
```

### Scalar::Util

Utility functions for scalars.

```python
su = perlthon.use("Scalar::Util")

su.looks_like_number("3.14")   # → truthy
su.looks_like_number("hello")  # → falsy
```

### Cwd

Get the current working directory.

```python
cwd = perlthon.use("Cwd")
print(cwd.cwd())       # → "/home/user/project"
print(cwd.abs_path("."))
```

### File::Spec

Portable file path operations.

```python
fs = perlthon.use("File::Spec")

# Note: File::Spec uses class methods
perlthon.call("File::Spec::catfile", "usr", "local", "bin")  # → "usr/local/bin"
```

## CPAN Modules

Any installed CPAN module can be loaded. Install modules with `cpan` or `cpanm` first:

```bash
cpanm JSON::XS Text::CSV DateTime
```

Then use them from Python:

```python
import perlthon

# Fast JSON encoding (if JSON::XS is installed)
perlthon.use("JSON::XS")
json_str = perlthon.eval('JSON::XS::encode_json({"key" => "value"})')

# CSV parsing
perlthon.use("Text::CSV")
# ... use Text::CSV functions
```

## Module Loading Patterns

### Check if a module is available

```python
import perlthon

def has_module(name: str) -> bool:
    try:
        perlthon.use(name)
        return True
    except RuntimeError:
        return False

if has_module("JSON::XS"):
    json = perlthon.use("JSON::XS")
else:
    json = perlthon.use("JSON::PP")  # Pure-Perl fallback
```

### Reuse module references

```python
import perlthon

# Load once, use many times
posix = perlthon.use("POSIX")

results = [posix.floor(x) for x in [1.1, 2.5, 3.9, 4.0]]
```

## Limitations

- **OO modules**: For modules requiring object instantiation, use `module.call("new", ...)` or `perlthon.eval()` with the full Perl syntax.
- **Import lists**: `perlthon.use()` loads the module but doesn't support selective imports (like `use Module qw(func1 func2)`). Use fully qualified names instead.
- **Tied variables**: Perl's tie magic is not directly exposed to Python.
