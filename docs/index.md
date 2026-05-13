# Perlthon

```{image} _static/logo.png
:alt: Perlthon Logo
:width: 400px
:align: center
```

```{toctree}
:maxdepth: 2
:caption: Contents

quickstart
api
modules
advanced
```

**Natively import and run Perl modules from Python** — powered by an embedded Perl
interpreter, with a Rust core via [PyO3](https://pyo3.rs).

## Why Perlthon?

Perl has decades of battle-tested modules on CPAN. Perlthon lets you use them
directly from Python without subprocess overhead, file-based IPC, or rewriting
anything.

```python
import perlthon

# Evaluate Perl code directly
perlthon.eval('"Hello " . "from Perl!"')  # → "Hello from Perl!"

# Load and use Perl modules
posix = perlthon.use("POSIX")
posix.floor(3.7)   # → 3.0
posix.ceil(3.2)    # → 4.0
```

## Features

- 🚀 **Zero-copy where possible** — Rust bridge minimizes overhead
- 📦 **Use any Perl module** — if it's installed, you can call it
- 🔀 **Automatic type conversion** — scalars, arrays, hashes map naturally
- 🛡️ **Error propagation** — Perl `die`/`croak` becomes Python exceptions
- 🐍 **Pythonic API** — attribute access for method calls, no boilerplate

## Installation

### Prerequisites

- Python ≥ 3.12
- Rust toolchain (for building from source)
- Perl development headers (`libperl-dev` on Debian/Ubuntu)
- `libcrypt-dev` (on Debian/Ubuntu)

### Install from source

```bash
pip install .
```

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
