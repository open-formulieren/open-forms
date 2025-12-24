.. _developers_backend_core_testing_tools:

============
Test helpers
============

Open Forms tests are built with the core Django testing helpers defined in
:mod:`django.test`, extended with some third party libraries and project-specific
helpers.

.. contents:: Helpers
   :depth: 3
   :local:
   :backlinks: entry

Third party packages
====================

* `django-webtest <https://pypi.org/project/django-webtest/>`_: acts more like a browser
  without being a full-blown browser. Very useful for admin tests, especially when
  combined with `pyquery <https://pypi.org/project/pyquery/>`_.
* `hypothesis <https://pypi.org/project/hypothesis/>`_: property based testing, very
  good for generating fuzzy data to catch edge cases you never would think of. See
  :ref:`developers_backend_core_testing_tools_hypothesis_strategies`.


Project helpers
===============

HTML assertions
---------------

.. automodule:: openforms.utils.tests.html_assert
   :members:

.. automodule:: openforms.utils.tests.webtest_base
   :members:

Frontend redirects
------------------

.. automodule:: openforms.frontend.tests
   :members:

Formio assertions
-----------------

.. automodule:: openforms.formio.tests.assertions
   :members:
   :undoc-members:

Recording HTTP traffic
----------------------

.. automodule:: openforms.utils.tests.vcr
   :members:

.. _developers_backend_core_testing_tools_hypothesis_strategies:

Custom Hypothesis strategies
----------------------------

General purpose strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: openforms.tests.search_strategies
   :members:
   :undoc-members:

Formio component strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: openforms.formio.tests.search_strategies
   :members:
   :undoc-members:
