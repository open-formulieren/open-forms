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

Metrics
-------

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

Traces
------

nginx provides the `ngx_otel_module <https://nginx.org/en/docs/ngx_otel_module.html>`_
for distributed tracing - which is not compiled/enabled by default. The Open Forms team
does not publish an image with this module enabled - you can opt-into doing this
yourself. Our `docker-compose.yml <https://github.com/open-formulieren/open-forms/tree/main/docker-compose.yml>`_ can provide inspiration.

Follow the upstream documentation on how to enable this - it should be pretty straight
forward to send the OTLP traces to the collector receiver since this is the same
mechanism as exporting the application-specific telemetry.

Flower
======

`Flower <https://flower.readthedocs.io/en/latest/prometheus-integration.html>`_ is a
Celery monitoring tool. It natively exposes Prometheus metrics, which you can scrape
with the OTel Collector `Prometheus receiver <https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/prometheusreceiver/README.md>`_.

Example configuration:

.. code-block:: yaml

    receivers:
      otlp: ...

      prometheus:
        config:
          scrape_configs:
            - job_name: 'otel-flower'
              scrape_interval: 15s
              static_configs:
                - targets: ['celery-flower:5555']
              metrics_path: /metrics

    service:
      metrics:
        receivers: [otlp, prometheus]
        processors: [...]
        exporters: [...]
