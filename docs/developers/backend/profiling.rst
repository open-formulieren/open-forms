.. _developers_backend_profiling:

=====================
Performance profiling
=====================

Since Open Forms emphasizes good performance, we need tooling to measure performance.
There is no point in optimizing without knowing what you're optimizing for. Every
optimization should be preceded by a base-line profiling run, which provides the
information on where to optimize.

.. note:: The tooling discussed here is only enabled with the development settings. You
   should verify the results on the same dev-environment, as this keeps the hardware
   and configuration consistent.

Profiling plain HTML pages
==========================

Plain HTML pages follow the classic pattern of a request that gets rendered into a
template response, which is eventually displayed in the browser.

In development mode, `Django Debug Toolbar`_ (DjDT) is enabled by default. It provides a
side-panel with information on timings, SQL queries and where they originate.

Profiling API endpoints
=======================

DjDT is not suitable for API endpoints, because there is no HTML body being rendered,
thus the panel cannot be displayed. We use `Django Silk`_ instead for endpoint
profiling.

Django silk is not enabled by default, and you can only use it with the development
settings. To enable profiling, set the environment variable ``PROFILE`` to a truthy
value, e.g.:

.. code-block:: bash

    PROFILE=yes DEBUG=no python src/manage.py runserver

The profile data is available on http://localhost:8000/silk/. You can make the API
calls using Postman, and they'll show up in the Silk dashboard.

Silk provides information on total request time, how many and which SQL queries ran,
timings of the queries and what caused the queries to run.

General recommendations
=======================

Disable DEBUG mode
------------------

You should use ``DEBUG=no`` when profiling, which disables some Django internals that
can degrade performance and thus give skewed results. Most notably, in debug mode,
Django keeps track of the database queries in an array.

Queries are usually the bottleneck
----------------------------------

In most web-apps, the database is the bottleneck for performance. Large amounts of
queries, or big/complex queries should catch your attention. Especially repeating
queries are suspicious - often they can be mitigated using ``select_related`` or
``prefetch_related``.

Measure relative performance
----------------------------

Expressing performance gains in percentage is usually the most useful. Of course,
endpoints taking 5 or 10 seconds in total are both bad, so use common sense when
interpreting the results. However, it's interesting if you can attribute a 20% total
request time reduction and 90% less queries to a single change.

If you have profiling numbers in production, you can apply the relative gains in
performance to the production numbers to get a ballkpark figure of the production
performance.

.. _Django Debug Toolbar: https://django-debug-toolbar.readthedocs.io/en/latest/
.. _Django Silk: https://github.com/jazzband/django-silk
