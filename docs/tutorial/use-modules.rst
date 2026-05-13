Use Perl modules
=================

This part of the tutorial teaches you how to load Perl modules and call their
functions from Python.


Load a module
-------------

Use :func:`perlthon.use` to load a Perl module. This is equivalent to Perl's
``use Module`` statement:

.. code-block:: python

   import perlthon

   posix = perlthon.use("POSIX")

The returned object is a ``PerlModule`` proxy that lets you call the module's functions
as Python method calls.


Call module functions
---------------------

Call functions on a loaded module using attribute access:

.. code-block:: python

   posix = perlthon.use("POSIX")

   print(posix.floor(3.7))   # 3.0
   print(posix.ceil(3.2))    # 4.0
   print(posix.pow(2, 10))   # 1024.0

Each attribute access returns a callable that, when invoked, calls the corresponding
Perl function.


Use fully qualified names
-------------------------

You can also call functions by their fully qualified name using :func:`perlthon.call`:

.. code-block:: python

   perlthon.use("POSIX")
   result = perlthon.call("POSIX::floor", 9.9)
   print(result)  # 9.0

This pattern is useful when you need to call a function without keeping a reference to
the module object.


Use multiple modules
--------------------

Load as many modules as you need. They are all available for the lifetime of the Python
process:

.. code-block:: python

   posix = perlthon.use("POSIX")
   fb = perlthon.use("File::Basename")
   lu = perlthon.use("List::Util")

   print(posix.floor(1.5))                      # 1.0
   print(fb.basename("/usr/local/bin/perl"))     # perl
   print(lu.sum(1, 2, 3, 4, 5))                 # 15


Handle missing modules
----------------------

If a module is not installed, Perlthon raises a ``RuntimeError``:

.. code-block:: python

   try:
       perlthon.use("Nonexistent::Module")
   except RuntimeError as e:
       print(f"Module not found: {e}")


Next steps
----------

In the next part, you will learn how Perlthon converts data structures between Perl and
Python.
