.. meta::
   :description: Documentation for Perlthon, a library for importing and running Perl modules from Python.

Perlthon
========

**Perlthon** natively imports and runs Perl modules from Python — powered by an
embedded Perl interpreter, with a Rust core via `PyO3 <https://pyo3.rs>`__.

Perlthon lets you use any installed Perl module directly from Python without subprocess
overhead, file-based IPC, or rewriting anything. Scalars, arrays, and hashes are
automatically converted between the two languages.

Perlthon is for Python developers who need to leverage existing Perl modules, system
administrators bridging Perl and Python toolchains, and anyone migrating from Perl to
Python incrementally.

---------

In this documentation
---------------------

.. grid:: 1 1 2 2

   .. grid-item-card:: Tutorial
      :link: tutorial/index
      :link-type: doc

      **Start here** — a hands-on introduction to Perlthon for new users

   .. grid-item-card:: How-to guides
      :link: how-to/index
      :link-type: doc

      **Step-by-step guides** covering key operations and common tasks

   .. grid-item-card:: Reference
      :link: reference/index
      :link-type: doc

      **Technical information** — API, type mappings, and configuration

   .. grid-item-card:: Explanation
      :link: explanation/index
      :link-type: doc

      **Discussion and clarification** of key topics and design decisions

---------

Project and community
---------------------

Perlthon is an open source project that warmly welcomes community contributions,
suggestions, fixes, and constructive feedback.

* `GitHub repository <https://github.com/lengau/perlthon>`__
* `Issue tracker <https://github.com/lengau/perlthon/issues>`__


.. toctree::
   :hidden:
   :maxdepth: 2

   tutorial/index
   how-to/index
   reference/index
   explanation/index
