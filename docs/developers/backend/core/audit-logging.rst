.. _developers_backend_core_audit_logging:

=============
Audit logging
=============

Open Forms has audit logging. The goals of the audit logging setup are:

* (functional) administrators can reconstruct what happened in and to a form submission
* GDPR (Dutch: AVG) questions like "who looked at this sensitive data" can be answered
* logs can help in debugging issues
* being easy to use for developers

.. contents:: Contents
   :depth: 3
   :local:
   :backlinks: none

Architecture
============

Audit logs are produced by using the ``openforms_audit`` logger. Logs can be produced
with any level ranging from ``DEBUG`` to ``CRITICAL`` - none will be dropped because
of their log level being too low.

Audit logs are routed to two destinations:

* the standard log output destination, where non-audit-logs also go. Normally this is
  ``stdout``/``stderr``, but configuration allows for writing to log files as an
  alternative.
* the database, in particular the generic log entry table from django-timeline-logger.

Logs that are routed to the database get processed by our adapter
:func:`openforms.logging.adapter.from_structlog`, which takes the event dict produced
by our logger and builds the necessary context to save into the
:class:`openforms.logging.models.TimelineLogProxy` model, such as:

* the event that triggered the log and associated display template
* the user that performed the action that was logged
* the object on which the action was performed
* additional metadata about the action, typically accessed in the event-specific
  display template

The log handler from django-timeline-logger does this in a way that's both performant
and robust - audit logs will still be written to the database even if the DB transaction
in the main thread rolls back.

Additionally, the ``stdout``/``stderr`` destination also receives all log events and is
even more reliable. DevOps roles should set up log aggregation with tools like Loki and
Grafana (see also: :ref:`observability (logging) <installation_observability_logging>`).
When conflicting information originates from logging to both destinations, you should
favour the ``stdout``/``stderr`` logs.

Usage and conventions
=====================

Developers can start audit logging right away with a couple of lines of code, for
example:

.. code-block:: python
    :linenos:
    :emphasize-lines: 3, 7, 21-32

    # views.py

    from openforms.logging import audit_logger

    def my_view(request: HttpRequest):
        ...
        audit_logger.info("my_view_accessed", user=request.user.username)
        ...
        return HttpResponse(...)

    # src/openforms/logging/adapter.py

    def from_structlog(event_dict: EventDict) -> EventDetails:
        from openforms.accounts.models import User

        ...

        match event_dict:
            ...

            case {
                "event": "my_view_accessed" as event,
                "user": str(username),
            }:
                user = User.objects.get(username=username)
                return EventDetails(
                    event=event,
                    instance=user,
                    user=user,
                    tags=[TimelineLogTags.avg],
                    extra_data={"context": "docs-example"},
                )

            ...

Note that:

* ``audit_logger`` can be called directly with the event and additional context
* you can use any log level that's best suited for the situation being logged
* any additional keyword arguments like ``user`` are passed in the event dict, and
  you can/should match against them

Conventions
-----------

* At the time of writing, we opt to only pass primitives like strings, numbers,
  booleans... as additional context in logging calls. When the logs are formatted for
  the console output, the string representation is taken of each member, and for model
  instances or even ``UUID`` instances, that leads to hard-to-scan/read output.

  .. note:: This *could* be addressed in the future with a custom structlog processor.

* When referring to a submission, use the ``submission_uuid=str(submission.uuid)`` kwarg.

* When referring to a Django user, use the ``username=user.username`` kwarg. If this is
  ambiguous (see the hijack audit logs), use the username as value, but pick a more
  appropriate keyword argument name.

* If you're unsure whether a convention exists or not, scan
  :func:`openforms.logging.adapter.from_structlog` for pre-existing patterns.

When to audit log?
------------------

* Important steps/phases in the lifecycle of a submission. Make sure to log start,
  (possible) skip, done and error events. Submission audit logs are displayed in the
  admin page when viewing a submission - functional administrators use this as a debug
  tool.
* Anything that can be privacy-sensitive. Make sure to log *who* accessed information
  from *where* or *what*, and if known, what the reason was.

.. seealso:: :ref:`developers_backend_logging` documentation.
