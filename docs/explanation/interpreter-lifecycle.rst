Interpreter lifecycle
=====================

This page explains how the embedded Perl interpreter is managed.


Singleton interpreter
---------------------

Perlthon creates a single Perl interpreter instance on first use. This interpreter
persists for the lifetime of the Python process.

.. code-block:: python

   import perlthon

   # First call creates the interpreter
   perlthon.eval("1")

   # All subsequent calls reuse the same interpreter
   perlthon.use("POSIX")
   perlthon.eval("POSIX::floor(3.7)")


Implications
------------

Because the interpreter is a singleton:

- **Module state persists.** Once a module is loaded with ``use``, it stays loaded.
  You do not need to call ``use`` again in subsequent code.

- **Global variables persist.** Any Perl global state set during one ``eval`` call is
  visible to subsequent calls.

- **No parallel interpreters.** Perl's interpreter is not designed for multiple
  instances in the same process. Perlthon follows this constraint.


Thread safety
-------------

The Perl interpreter is not thread-safe. Perlthon relies on Python's GIL to serialise
access. In practice, this means:

- Calling Perlthon from multiple Python threads is safe (the GIL prevents concurrent
  access).
- Perlthon should not be used with ``nogil`` builds of Python without external
  synchronisation.
