.. _developers_backend_logging:

=======
Logging
=======

Logging is the practice of adding strategic log statements in the code to inform of
particular events taking place. It's generally a good practice to make debugging
certain data-flows easier and can provide insight in what the system is doing. Logs can
also be critical audit-information, see :ref:`developers_backend_core_audit_logging`.

Logs are typically emitted during development (with ``runserver``) but also in
production (containers). In the latter situation, logs are usually scraped and aggregated
by the infrastructure layer (Kubernetes, Docker on a virtual machine...) and made
available in some visualization tool, like Grafana.

Log tooling
===========

While Python provides the ``logging`` module in the standard library, we've opted to
use ``structlog`` instead to really emphasize good practices for structured, rich logs
that can be correlated. They are emitted as JSON (or key=value pairs, if desired). In
development, this means we get nice colored output.

.. tip:: Install the ``rich`` package in your dev environment for even nicer output,
   particularly tracebacks.

.. note:: Structlog wraps the stdlib logs emitted from third party packages, so we get
   the best of both worlds.

The general patterns with structlog are:

.. code-block:: python

    import structlog

    logger = structlog.stdlib.get_logger(__name__)

    def my_func():
        with structlog.contextvars.bound_contextvars(module="example"):
            result = helper_func("foo")
            logger.debug("result_received", result=result)
        return result

    def helper_func(arg: str) -> str:
        log = logger.bind(arg=arg)
        log.info("argument_received")
        return arg

1. ``import structlog`` instead of ``import logging``. There is a Ruff check to prevent
   accidents.
2. Events are simple strings with underscores - do not interpolate anything! Instead,
   provide keyword arguments - they will be emitted together with the log event. This
   is much easier to parse and query in log aggregation tools.
3. You can create a bound logger with ``log = logger.bind(**kwargs)``. Any additional log
   statements from ``log`` will include the additional context that was bound - meaning
   you can bind variables once without needing to pass them along everywhere or repeat
   them.
4. You can bind context variables across multiple calls using the context manager.
   Downstream logger calls will include the context specified by the context manager,
   and it will automatically unset them again.

Log levels
==========

The following log levels may be used, with a description of when they're appropriate
to use.

By default, log levels INFO and above are emitted.

``DEBUG``
    Use with ``logger.debug(...)``. Generally not interesting unless you need to debug
    the particular feature and users opt-in to this low log level. Put information under
    this level that should only be displayed when chasing down a problem.

``INFO``
    General informative events that show the system is operating within normal parameters.
    They don't warrant any actions, it's just "good to know" that *a thing* is happening.
    Don't overuse this, as these log records are emitted by default and could create a lot
    of noise.

``WARNING``
    Use ``logger.warning(...)`` for non-fatal problems that probably require someone to
    take some action. It's a good candidate for situations that should not happen, yet
    when they do you want to know so you can fix the root cause.

``ERROR``
    Use ``logger.error`` for suppressed errors that have an impact on the end-user(s).
    For example, an external service is down or not operating as expected and prefill
    is not working. These log records can be used to pinpoint what went wrong and when,
    while still allowing the user to complete the form but with a worse user experience.

``EXCEPTION``
    Same as error above, except it will automatically grab the exception information if
    not provided explicitly.


Passing exception information
=============================

Specify the ``exc_info=True`` or ``exc_info=some_exception_instance`` kwarg to pass
along exception information, if you have one. This can be very useful for the warning
and error log levels. The exception log level will grab the exception by default, but
there's no harm in passing the exception manually either.

Log events and extra context
============================

Coming up with a good name for a log event is probably the hardest. You can take some
inspiration from ``django_structlog``, which emits request events like:

* ``request_started``
* ``request_finished``

Event names like ``start_pdf_generation`` are also acceptable, as they can sometimes
be more natural.

For certain Open Forms modules, it can be beneficial to apply some namespacing to
identify which part of the application is emitting logs, for example:

.. code-block:: python

    logger.info("authentication.start_flow")

For the extra context, there are some "typical" keys that you can use to get a consistent
log pattern:

* ``module``, for example ``authentication``, ``registrations``, ``prefill``. Helps
  filtering down log events emitted by a particular part of functionality in Open Forms.
* ``reason``, common with ``skip_FOO`` events. The event is that some operation was
  skipped, but a quick look at the reason for skipping in the logs can be very useful.
* ``outcome``, when something is detected or handled in a particular way, you can provide
  a hint to the result, e.g. ``ignore`` or ``skip`` or even ``success``.
* ``action``, a useful context variable that can act as a grouper for log records,
  typically set via ``structlog.contextvars.bound_contextvars``
* ``plugin``, Open Forms knows many plugins, being able to trace down at a higher level
  which log records originate from where can be informative.
