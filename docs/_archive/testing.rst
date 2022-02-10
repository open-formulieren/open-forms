.. _testing:

=======
Testing
=======

This document covers the tools to run tests and how to use them.


Django tests
============

Run the project tests by executing::

    $ python src/manage.py test src --keepdb

To measure coverage, use ``coverage run``::

    $ coverage run src/manage.py test src --keepdb

It may be convenient to add some aliases::

    $ alias runtests='python src/manage.py test --keepdb'
    $ runtests src

and::

    $ alias cov_runtests='coverage run src/manage.py test --keepdb'
    $ cov_runtests src && chromium htmlcov/index.html
