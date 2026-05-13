System requirements
===================

This page lists the requirements for building and running Perlthon.


Runtime requirements
--------------------

- Python 3.12 or later
- Perl 5 (any recent version)
- A shared ``libperl`` library


Build requirements
------------------

- Rust toolchain (stable)
- Perl development headers:

  - Debian/Ubuntu: ``libperl-dev``, ``libcrypt-dev``
  - Fedora/RHEL: ``perl-devel``

- Python build frontend (``pip``, ``build``, or ``maturin``)


Supported platforms
-------------------

Perlthon is tested on Linux. Other Unix-like platforms (macOS, FreeBSD) may work but
are not officially supported.
