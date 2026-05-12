# Perlthon 🐪🐍

Natively import and run Perl modules from Python — powered by an embedded Perl
interpreter, with a Rust core via [PyO3](https://pyo3.rs).

## Quick Start

```python
import perlthon

# Evaluate Perl code directly
perlthon.eval('"Hello " . "from Perl!"')  # → "Hello from Perl!"

# Load and use Perl modules
posix = perlthon.use("POSIX")
posix.floor(3.7)   # → 3.0
posix.ceil(3.2)    # → 4.0

# Call fully qualified Perl functions
perlthon.call("POSIX::floor", 3.7)  # → 3.0
```

## Installation

### Prerequisites

- Python ≥ 3.12
- Rust toolchain (for building)
- Perl development headers (`libperl-dev` on Debian/Ubuntu, `perl-devel` on
  Fedora/RHEL)
- `libcrypt-dev` (on Debian/Ubuntu)

### From source

```bash
pip install .
```

### Development

```bash
uv sync
uv run pytest
```

## API

### `perlthon.use(module_name: str) -> PerlModule`

Load a Perl module (like Perl's `use`). Returns a `PerlModule` proxy object
where attribute access maps to function calls in that module's namespace.

```python
json = perlthon.use("JSON::PP")
```

### `perlthon.eval(code: str) -> PerlValue`

Evaluate a string of Perl code and return the result, converted to a Python
type.

```python
perlthon.eval('[1, 2, 3]')         # → [1, 2, 3]
perlthon.eval('{"a" => 1}')        # → {"a": 1}
```

### `perlthon.call(function_name: str, *args) -> PerlValue`

Call a Perl function by its fully qualified name.

```python
perlthon.call("POSIX::floor", 3.7)  # → 3.0
```

### `PerlModule`

Proxy object returned by `use()`. Attribute access creates callable references
to functions in the module's namespace.

```python
posix = perlthon.use("POSIX")
posix.floor(3.7)  # calls POSIX::floor(3.7)
```

For OO-style method dispatch (passing the module as invocant):

```python
posix.call("floor", 3.7)  # calls POSIX->floor(3.7)
```

## Type Mapping

| Python              | Perl            |
|---------------------|-----------------|
| `str`               | String scalar   |
| `int`               | Integer scalar  |
| `float`             | Float scalar    |
| `bool`              | `$true`/`$false`|
| `None`              | `undef`         |
| `list`              | Array reference |
| `dict`              | Hash reference  |

## Architecture

```
Python  ←→  perlthon (Python)  ←→  _core (Rust/PyO3)  ←→  perl_glue.c  ←→  libperl
```

- **`perlthon/`** — Pure Python API layer (`use`, `eval`, `call`, `PerlModule`)
- **`src/lib.rs`** — Rust FFI bindings + PyO3 wrapper classes
- **`csrc/perl_glue.c`** — C wrapper around Perl's macro-heavy embedding API
- **`build.rs`** — Build script that discovers Perl and compiles the C glue

## License

TBD