Why Perlthon?
=============

This page explains the motivation for Perlthon and when it is a good fit.


The problem
-----------

Perl has decades of battle-tested modules on CPAN — text processing, system
administration, bioinformatics, legacy business logic. When working in Python, accessing
this code typically requires one of:

- **Subprocess calls** — slow, fragile, limited to string I/O.
- **File-based IPC** — cumbersome, requires serialisation.
- **Rewriting in Python** — expensive and error-prone for complex modules.


The solution
------------

Perlthon embeds a real Perl interpreter in the Python process and provides a direct
bridge between the two runtimes. This means:

- **No process overhead.** Function calls happen in-process.
- **Native types.** Scalars, arrays, and hashes are converted automatically.
- **Full Perl.** Any valid Perl code works, including regex, closures, and modules.


When to use Perlthon
--------------------

Perlthon is a good fit when:

- You need to use a Perl module that has no Python equivalent.
- You are incrementally migrating a codebase from Perl to Python.
- You want to use Perl's text processing strengths (regex, split, join) from Python.
- You maintain a system that combines Perl and Python components.


When not to use Perlthon
------------------------

Perlthon may not be the best choice when:

- A pure-Python alternative exists and meets your performance needs.
- You need to run Perl code in parallel across multiple threads (Perl's interpreter is
  single-threaded).
- You are deploying to an environment where Perl is not available.
