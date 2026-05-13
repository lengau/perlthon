Use CPAN modules
=================

This guide explains how to use third-party Perl modules from CPAN with Perlthon.


Install CPAN modules
--------------------

Perlthon can use any Perl module installed on the system. To let Perlthon
manage installation, use :mod:`perlthon.cpan`:

.. code-block:: python

   from perlthon import cpan

   cpan.install("JSON::XS", "Text::CSV", "DateTime")

If you prefer, you can still preinstall modules with ``cpanm`` or ``cpan``.


Security model for ``perlthon.cpan.install()``
----------------------------------------------

``perlthon.cpan.install()`` does not trust ambient CPAN mirror configuration.
It always pins ``cpanm`` to ``https://cpan.metacpan.org`` by default, ignores
``PERL_CPANM_*`` environment variables, and enables ``cpanm --verify`` when
that flag is available in the installed ``cpanm``.

To use an internal mirror, pass an explicit HTTPS URL:

.. code-block:: python

   from perlthon import cpan

   cpan.install("JSON::XS", mirror="https://cpan.example.com")


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
