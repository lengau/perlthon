Handle errors
=============

This guide explains how Perl errors are surfaced in Python and how to handle them.


Catch Perl exceptions
---------------------

When Perl code calls ``die`` or ``croak``, Perlthon raises a Python ``RuntimeError``:

.. code-block:: python

   import perlthon

   try:
       perlthon.eval('die "something went wrong"')
   except RuntimeError as e:
       print(f"Caught: {e}")


Detect missing modules
----------------------

A failed ``use`` raises a ``RuntimeError``. Use this to check availability:

.. code-block:: python

   def has_module(name: str) -> bool:
       try:
           perlthon.use(name)
           return True
       except RuntimeError:
           return False


Provide fallbacks
-----------------

Use error handling to select between alternative modules:

.. code-block:: python

   try:
       json = perlthon.use("JSON::XS")
   except RuntimeError:
       json = perlthon.use("JSON::PP")


Handle syntax errors
--------------------

Syntax errors in ``eval`` are also raised as ``RuntimeError``:

.. code-block:: python

   try:
       perlthon.eval("if (")
   except RuntimeError as e:
       print(f"Syntax error: {e}")
