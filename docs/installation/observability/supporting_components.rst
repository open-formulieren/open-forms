.. _installation_observability_supporting_components:

=================================
Observing supporting applications
=================================

Open Forms uses a number of extra components/software applications which are not
developed by the Open Forms development team. Typically you'll also want to add
observability to these components as they may be a point of failure.

In this documentation section, you find some recommendations on how to make them
observable. We assume that you're using `OTel Collector <https://opentelemetry.io/docs/collector/>`_
to ingest telemetry data.

PostgreSQL
==========

Open Forms persists its data in a relational PostgreSQL database. The database (cluster)
can also be observed. Possibly your managed hosting provider already exports metrics,
and if not, you can use the
`PostgreSQL Receiver <https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/postgresqlreceiver>`_
contrib package from OTel Collector.

Example configuration:

.. code-block:: yaml

    receivers:
      otlp: ...

      postgresql:
        endpoint: "db:5432"
        transport: tcp
        username: otelu
        password: supersecret
        databases:
          - openforms
        tls:
          insecure: true

    service:
      metrics:
        receivers: [otlp, postgresql]
        processors: [...]
        exporters: [...]

It's not relevant if the database is running as a container, on the host system or in
some managed hosting environment as long as the collector can connect to it with the
right privileges (see the contrib package documentation for details).

Redis
=====

:ref:`Redis <installation_redis>` (or alternatively `Valkey <https://valkey.io/>`_) acts
as cache and message broker.

The OTel Collector contrib package supports extracting metrics from Redis instances through the
`Redis Receiver <https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/redisreceiver/README.md>`_.

Example configuration:

.. code-block:: yaml

    receivers:
      otlp: ...

      redis:
        endpoint: "my-redis-service:6379"
        tls:
          insecure: true

    service:
      metrics:
        receivers: [otlp, redis]
        processors: [...]
        exporters: [...]

The receiver will periodically scrape the redis instance(s). Adapt the configuration as
needed for the correct host name and possible authentication credentials.

nginx
=====

nginx is used as reverse proxy and for serving binary files. The OTel Collector contrib
package supports extracting some basic metrics by leveraging the "stub status" module,
via the `nginx receiver <https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/nginxreceiver>`_.

Example configuration:

.. code-block:: yaml

    receivers:
      otlp: ...

      redis:
        endpoint: "nginx:8080/_status"

    service:
      metrics:
        receivers: [otlp, nginx]
        processors: [...]
        exporters: [...]
