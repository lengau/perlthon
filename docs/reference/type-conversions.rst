Type conversions
================

This page documents how values are converted between Perl and Python.


Perl to Python
--------------

.. list-table::
   :header-rows: 1
   :widths: 40 40 20

   * - Perl type
     - Python type
     - Example
   * - Integer scalar
     - ``int``
     - ``42``
   * - Float scalar
     - ``float``
     - ``3.14``
   * - String scalar
     - ``str``
     - ``"hello"``
   * - ``undef``
     - ``None``
     -
   * - Array reference
     - ``list``
     - ``[1, 2, 3]``
   * - Hash reference
     - ``dict``
     - ``{"k": "v"}``


Python to Perl
--------------

.. list-table::
   :header-rows: 1
   :widths: 40 40 20

   * - Python type
     - Perl type
     - Example
   * - ``int``
     - Integer scalar
     - ``42``
   * - ``float``
     - Float scalar
     - ``3.14``
   * - ``str``
     - String scalar
     - ``"hello"``
   * - ``None``
     - ``undef``
     -
   * - ``list``
     - Array reference
     -
   * - ``dict``
     - Hash reference
     -


Notes
-----

- Perl's boolean values are represented as integers (``1`` for true, ``""`` or ``0``
  for false).
- Hash keys are always strings in Perl; non-string keys passed from Python are
  converted.
- Nested data structures are converted recursively.
