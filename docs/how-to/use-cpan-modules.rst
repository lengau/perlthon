Use CPAN modules
=================

This guide explains how to use third-party Perl modules from CPAN with Perlthon.


Install CPAN modules
--------------------

Perlthon can use any Perl module installed on the system. Install modules with
``cpanm`` (recommended) or ``cpan``:

.. code-block:: bash

   cpanm JSON::XS Text::CSV DateTime


Use installed modules
---------------------

Once installed, use them exactly like core modules:

.. code-block:: python

   import perlthon

   perlthon.use("JSON::XS")
   json_str = perlthon.eval('JSON::XS::encode_json({"key" => "value"})')


Check module availability at runtime
-------------------------------------

Not all systems have the same CPAN modules installed. Check before using:

.. code-block:: python

   import perlthon

   def require_module(name: str):
       try:
           return perlthon.use(name)
       except RuntimeError:
           raise ImportError(
               f"Perl module {name!r} is not installed. "
               f"Install it with: cpanm {name}"
           )

   csv = require_module("Text::CSV")
