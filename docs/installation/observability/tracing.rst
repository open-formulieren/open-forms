.. _installation_observability_tracing:

=======
Tracing
=======

Tracing makes it possible to follow the flow of requests across system boundaries,
e.g. from one application to another. This makes it possible to pinpoint where errors
or performance degrations are situated exactly. Trace IDs also make it possible to
correlate the relevant log entries.

Since Open Forms 3.5, we have distributed tracing support. Open Forms will propagate
traces that it receives from upstream services, and down to calls into other services
like:

* PostgreSQL database
* Redis (cache + message queue)
* External HTTP requests

.. versionadded:: 3.5.0

   Added support for distributed tracing and trace propagation.
