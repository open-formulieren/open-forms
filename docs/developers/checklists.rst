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

Testing on mobile
=================

To test a form on mobile:

- In the ``.env`` file for the Open Forms backend, add the local network address on which the SDK will run to
  the ``CORS_ALLOWED_ORIGINS`` (for example: ``CORS_ALLOWED_ORIGINS=http://192.168.42.203:3000``)
- Run the backend server with ``python src/manage.py runserver 0.0.0.0:8000``.
- In the ``.env.local`` of the SDK add the local network address of the backend to the ``REACT_APP_BASE_API_URL``
  (for example, ``REACT_APP_BASE_API_URL=http://192.168.42.203:8000/api/v1/``).

