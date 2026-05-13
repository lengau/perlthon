API reference
=============

This page documents the public API of the ``perlthon`` Python package.


Module-level functions
----------------------

.. function:: perlthon.eval(code: str) -> PerlValue

   Evaluate a string of Perl code and return the result.

   :param code: Perl source code to evaluate.
   :returns: The result of the evaluation, converted to a Python type.
   :raises RuntimeError: If the Perl code has a syntax error or calls ``die``.

.. function:: perlthon.use(module_name: str) -> PerlModule

   Load a Perl module (equivalent to Perl's ``use Module``).

   :param module_name: Fully qualified Perl module name (for example, ``"Text::CSV"``).
   :returns: A :class:`PerlModule` proxy that supports method calls.
   :raises RuntimeError: If the module cannot be found or loaded.

.. function:: perlthon.call(function_name: str, *args) -> PerlValue

   Call a Perl function by its fully qualified name.

   :param function_name: For example, ``"POSIX::floor"``.
   :param args: Arguments to pass to the Perl function.
   :returns: The return value from Perl, converted to a Python type.


CPAN helpers
------------

.. function:: perlthon.cpan.install(*modules: str, lib: str | None = None, mirror: str | None = None) -> None

   Install one or more CPAN modules with ``cpanm``.

   Perlthon pins installs to ``https://cpan.metacpan.org`` by default,
   ignores ambient ``PERL_CPANM_*`` configuration, requires HTTPS mirror
   overrides, and enables ``cpanm --verify`` when the local ``cpanm``
   supports it.


Classes
-------

.. class:: PerlModule

   A loaded Perl module, supporting attribute-based method calls. Returned by
   :func:`perlthon.use`.

   Accessing an attribute returns a :class:`PerlCallable`:

   .. code-block:: python

      posix = perlthon.use("POSIX")
      posix.floor(3.7)  # calls POSIX::floor

   .. method:: call(method: str, *args) -> PerlValue

      Call a method using OO-style dispatch (passes the module as invocant).

.. class:: PerlCallable

   A lazy reference to a Perl function. Calling it invokes the function using its
   fully qualified name.

   .. code-block:: python

      posix = perlthon.use("POSIX")
      floor_fn = posix.floor    # PerlCallable
      result = floor_fn(3.7)    # calls POSIX::floor


Type alias
----------

.. data:: PerlValue

   The type of values returned from Perl:

   .. code-block:: python

      type PerlValue = str | int | float | bool | list[Any] | dict[str, Any] | None
