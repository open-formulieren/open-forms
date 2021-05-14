.. _coding_style_backend:

=====================
Backend coding style
=====================

The `django coding style`_ is the basis for this styleguide. Some sections dive
a bit deeper or put extra emphasis.

Imports
=======

In short: use `isort`_ to check your import ordering. The config file is in
``.isort.cfg``.

Order and group your imports

* Use relative imports for your django app
* Ordering:
    - future
    - standard libraries
    - Django components
    - third party libraries
    - project imports
    - local (app) imports

Example:

.. code-block::

    import datetime
    from datetime import timedelta

    import django.contrib.admin

    import openforms.other_app.models

    from .models import SomeModel

Naming
======

* Use plural form for apps. E.g.: ``accounts``, not ``account``.

* Use singular form for model, view and form class

Example:

.. code-block::

    from openforms.accounts.models import Account

    class Idea(models.Model):
        pass

    class IdeaForm(forms.ModelForm):
        pass

    class IdeaDetailView(views.DetailView):
        pass


.. _django coding style: https://docs.djangoproject.com/en/stable/internals/contributing/writing-code/coding-style/
.. _isort: https://pypi.python.org/pypi/isort
