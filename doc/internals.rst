
===========
 Internals
===========

.. automodule:: clik_wtforms


Form
====

.. autoclass:: Form
   :show-inheritance:
   :members:
   :private-members:
   :special-members:
   :exclude-members: print_errors

   .. automethod:: print_errors(file=sys.stderr)


Fields
======

.. autoclass:: DateField
   :show-inheritance:
   :members:
   :special-members:

.. autoclass:: DateTimeField
   :show-inheritance:
   :members:
   :special-members:

.. autoclass:: DecimalField
   :show-inheritance:
   :members:
   :special-members:

.. autoclass:: FieldList
   :show-inheritance:
   :members:
   :special-members:

.. autoclass:: FloatField
   :show-inheritance:
   :members:
   :special-members:

.. autoclass:: IntegerField
   :show-inheritance:
   :members:
   :special-members:

.. autoclass:: SelectField
   :show-inheritance:
   :members:
   :special-members:

.. autoclass:: SelectMultipleField
   :show-inheritance:

.. autoclass:: StringField
   :show-inheritance:
   :members:
   :special-members:


Miscellany
==========

.. autodata:: __version__

.. autofunction:: default

.. autofunction:: stringify

.. autoexception:: FormError

.. autoclass:: Multidict
   :show-inheritance:
   :members:
   :special-members:
   :exclude-members: __weakref__

.. autodata:: COMMON_DEFAULT_CALLABLES
   :annotation:

.. autodata:: EXAMPLE_DATETIME

.. autodata:: DATETIME_TYPES
   :annotation:

.. autodata:: MULTIPLE_VALUE_TYPES
   :annotation:

.. autodata:: PRIMITIVE_TYPES
   :annotation:

.. autodata:: SELECT_TYPES
   :annotation:

.. autodata:: SIMPLE_TYPES
   :annotation:
