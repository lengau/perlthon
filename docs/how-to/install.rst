Install Perlthon
================

This guide covers installing Perlthon from source.


Install system dependencies
---------------------------

Perlthon requires Perl development headers and a Rust toolchain.

On Debian or Ubuntu:

.. code-block:: bash

   sudo apt-get install libperl-dev libcrypt-dev

On Fedora or RHEL:

.. code-block:: bash

   sudo dnf install perl-devel


Install the Rust toolchain
--------------------------

If you do not already have Rust installed:

.. code-block:: bash

   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh


Install Perlthon
----------------

From the repository root:

.. code-block:: bash

   pip install .


Set up a development environment
---------------------------------

For development, use `uv <https://docs.astral.sh/uv/>`__:

.. code-block:: bash

   uv sync
   uv run pytest
