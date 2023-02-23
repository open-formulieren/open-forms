.. _manual_known_problems:

============
Known issues
============

Repeating groups component
==========================

Duplicate keys
--------------

The keys of the components inside a repeating group should not duplicate the key of any component in the form.
Duplicate keys cause a problem in the case of file components, whose submission data needs to be extracted and used to
create a submission attachment file.

The current band aid for this problem is preventing to save a form with duplicate keys, but it should be fixed properly
in issue `#2758 <https://github.com/open-formulieren/open-forms/issues/2758>`_.
