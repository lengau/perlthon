Call Perl functions
===================

This guide explains the different ways to call Perl functions from Python.


Call a function by fully qualified name
---------------------------------------

Load the module first, then call the function with its full name:

.. code-block:: python

   import perlthon

   perlthon.use("POSIX")
   result = perlthon.call("POSIX::floor", 3.7)


Call a function via the module proxy
------------------------------------

Load the module and use attribute access:

.. code-block:: python

   posix = perlthon.use("POSIX")
   result = posix.floor(3.7)

This is equivalent to calling ``POSIX::floor`` but provides a more Pythonic interface.


Call an OO-style method
-----------------------

For modules that use object-oriented dispatch, use the ``call`` method on the module
proxy:

.. code-block:: python

   mod = perlthon.use("Some::OO::Module")
   mod.call("new", arg1, arg2)

This passes the module name as the invocant, which is required for class methods in
Perl's OO system.


Evaluate complex expressions
-----------------------------

For expressions that don't map neatly to a single function call, use ``eval``:

.. code-block:: python

   result = perlthon.eval("""
   do {
       my @sorted = sort { $b <=> $a } (5, 2, 8, 1, 9);
       [@sorted]
   }
   """)
