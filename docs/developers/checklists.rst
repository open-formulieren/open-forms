.. _developers_checklists:


=========================
Checklists for developers
=========================


Adding features to forms
========================

When you add a new feature to the ``forms`` module, make sure that the following features still work:

#. Importing / exporting forms in the admin
#. Bulk importing / exporting forms in the admin
#. Copying a form (both with the admin action from the form list page and with the button from the form detail page)

Also good to check that:

#. FormVariables behave as expected
#. Forms with reusable form definitions work as expected
