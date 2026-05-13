Work with data structures
=========================

This part of the tutorial teaches you how Perlthon handles complex Perl data structures.


Array references
----------------

Perl array references are returned as Python lists:

.. code-block:: python

   import perlthon

   nums = perlthon.eval("[1, 2, 3, 4, 5]")
   print(nums)        # [1, 2, 3, 4, 5]
   print(type(nums))  # <class 'list'>

You can use Perl's list operations and get the results as Python lists:

.. code-block:: python

   evens = perlthon.eval("[grep { $_ % 2 == 0 } (1..10)]")
   print(evens)  # [2, 4, 6, 8, 10]

   doubled = perlthon.eval("[map { $_ * 2 } (1, 2, 3)]")
   print(doubled)  # [2, 4, 6]


Hash references
---------------

Perl hash references are returned as Python dictionaries:

.. code-block:: python

   data = perlthon.eval('{"name" => "perl", "version" => 5}')
   print(data)           # {'name': 'perl', 'version': 5}
   print(data["name"])   # perl


Nested structures
-----------------

Nested combinations of arrays and hashes are fully supported:

.. code-block:: python

   nested = perlthon.eval('{"users" => [{"name" => "Alice"}, {"name" => "Bob"}]}')
   print(nested["users"][0]["name"])  # Alice

   matrix = perlthon.eval("[[1, 2], [3, 4], [5, 6]]")
   print(matrix[1][0])  # 3


Perl expressions that return structures
----------------------------------------

You can use ``do`` blocks for complex expressions:

.. code-block:: python

   result = perlthon.eval("""
   do {
       my @nums = (1..10);
       my @evens = grep { $_ % 2 == 0 } @nums;
       [map { $_ ** 2 } @evens]
   }
   """)
   print(result)  # [4, 16, 36, 64, 100]


Summary
-------

You have now completed the Perlthon tutorial. You can:

- Evaluate arbitrary Perl expressions
- Load and use Perl modules
- Work with complex data structures across the language boundary

For task-specific instructions, see the :doc:`/how-to/index`. For a complete API
description, see the :doc:`/reference/index`.
