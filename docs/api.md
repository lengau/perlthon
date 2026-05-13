# API Reference

Complete reference for the `perlthon` Python package.

## Module-Level Functions

### `perlthon.eval(code)`

Evaluate a string of Perl code and return the result.

```python
perlthon.eval("2 + 2")          # → 4
perlthon.eval('"hello"')        # → "hello"
perlthon.eval("[1, 2, 3]")      # → [1, 2, 3]
perlthon.eval("undef")          # → None
```

**Parameters:**
: **code** (*str*) — Perl source code to evaluate.

**Returns:**
: The result of the evaluation, converted to a Python type.

**Return type:**
: `str | int | float | bool | list | dict | None`

**Raises:**
: `RuntimeError` — If the Perl code contains a syntax error or calls `die`.

---

### `perlthon.use(module_name)`

Load a Perl module (equivalent to Perl's `use Module`).

```python
posix = perlthon.use("POSIX")
fb = perlthon.use("File::Basename")
```

**Parameters:**
: **module_name** (*str*) — Fully qualified Perl module name (e.g. `"Text::CSV"`).

**Returns:**
: A {class}`PerlModule` proxy object that supports method calls.

**Raises:**
: `RuntimeError` — If the module cannot be found or loaded.

---

### `perlthon.call(function_name, *args)`

Call a Perl function by its fully qualified name.

```python
perlthon.use("POSIX")
perlthon.call("POSIX::floor", 3.7)  # → 3.0
```

**Parameters:**
: **function_name** (*str*) — Fully qualified function name (e.g. `"POSIX::floor"`).
: **\*args** — Arguments to pass to the Perl function.

**Returns:**
: The return value from Perl, converted to a Python type.

**Return type:**
: `str | int | float | bool | list | dict | None`

---

## Classes

### `PerlModule`

A loaded Perl module, supporting attribute-based method calls.

Returned by {func}`perlthon.use`. You don't instantiate this directly.

```python
posix = perlthon.use("POSIX")
posix.floor(3.7)   # Calls POSIX::floor
posix.ceil(3.2)    # Calls POSIX::ceil
```

#### Methods

##### `PerlModule.call(method, *args)`

Call a method on this Perl module using OO-style dispatch (passes the module as invocant).

```python
mod = perlthon.use("Some::OO::Module")
mod.call("new", arg1, arg2)
```

**Parameters:**
: **method** (*str*) — Method name to call.
: **\*args** — Arguments to pass.

---

### `PerlCallable`

A lazy reference to a Perl function, returned when accessing attributes on a {class}`PerlModule`.

```python
posix = perlthon.use("POSIX")
floor_fn = posix.floor      # PerlCallable, not yet called
result = floor_fn(3.7)      # Now calls POSIX::floor
```

Calling a `PerlCallable` invokes the function using its fully qualified name
(e.g. `POSIX::floor`).

---

## Type Conversions

Perlthon automatically converts between Perl and Python types:

| Perl Type        | Python Type   |
|------------------|---------------|
| Integer scalar   | `int`         |
| Float scalar     | `float`       |
| String scalar    | `str`         |
| `undef`          | `None`        |
| Array reference  | `list`        |
| Hash reference   | `dict`        |

### Passing Python → Perl

| Python Type | Perl Type       |
|-------------|-----------------|
| `int`       | Integer scalar  |
| `float`     | Float scalar    |
| `str`       | String scalar   |
| `None`      | `undef`         |
| `list`      | Array reference |
| `dict`      | Hash reference  |
