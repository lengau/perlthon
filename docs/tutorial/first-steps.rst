First steps with Perlthon
=========================

This part of the tutorial teaches you how to evaluate Perl expressions from Python.


Import and evaluate
-------------------

Start a Python session and import Perlthon:

.. code-block:: python

   import perlthon

Evaluate a simple Perl expression:

.. code-block:: python

   result = perlthon.eval("2 + 2")
   print(result)  # 4

Perlthon evaluates the expression using a real embedded Perl interpreter and returns
the result as a native Python object.


Work with strings
-----------------

Perl string operations work as expected:

.. code-block:: python

   greeting = perlthon.eval('"Hello, " . "World!"')
   print(greeting)  # Hello, World!

   repeated = perlthon.eval('"ha" x 3')
   print(repeated)  # hahaha

   upper = perlthon.eval('uc("whisper")')
   print(upper)  # WHISPER


Handle undefined values
-----------------------

Perl's ``undef`` maps to Python's ``None``:

.. code-block:: python

   result = perlthon.eval("undef")
   print(result)  # None


Handle errors
-------------

If the Perl code contains an error, Perlthon raises a ``RuntimeError``:

.. code-block:: python

   try:
       perlthon.eval('die "something broke"')
   except RuntimeError as e:
       print(f"Perl error: {e}")

This also applies to syntax errors and strict-mode violations.


Next steps
----------

In the next part, you will learn how to load and use Perl modules.
