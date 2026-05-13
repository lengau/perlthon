Architecture
============

This page explains how Perlthon is structured internally.


Layer diagram
-------------

Perlthon has three layers:

#. **Python API** (``src/perlthon/__init__.py``) — the public interface that users
   import. Provides ``eval``, ``use``, ``call``, ``PerlModule``, and ``PerlCallable``.

#. **Rust bridge** (``src/lib.rs``) — a PyO3 extension module that exposes the
   ``PerlInterpreter`` class to Python. Handles argument marshalling and error
   conversion.

#. **C embedding layer** (``csrc/``) — directly links against ``libperl`` and
   provides functions for evaluating code, calling functions, and converting Perl
   SVs to Rust types.


Data flow
---------

When you call ``perlthon.eval("2 + 2")``:

#. The Python layer obtains the singleton ``PerlInterpreter`` instance.
#. It calls ``PerlInterpreter.eval("2 + 2")`` on the Rust extension.
#. The Rust code passes the string to the C layer via FFI.
#. The C layer calls ``eval_pv()`` in the embedded Perl interpreter.
#. The resulting Perl SV is inspected and converted to a Rust value.
#. The Rust layer converts the value to a Python object via PyO3.
#. The Python object is returned to the caller.


Why Rust and C?
---------------

- **C** is necessary because Perl's embedding API (``perlembed``) is a C API. The
  ``csrc/`` layer provides a thin, safe wrapper around the raw Perl macros.

- **Rust** is used for the Python ↔ C bridge because PyO3 makes it straightforward to
  write safe, ergonomic Python extensions. It handles reference counting, error
  propagation, and type conversion between Python and native code.
