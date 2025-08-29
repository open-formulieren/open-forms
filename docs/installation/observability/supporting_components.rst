.. _installation_observability_supporting_components:

=================================
Observing supporting applications
=================================

Open Forms uses a number of extra components/software applications which are not
developed by the Open Forms development team. Typically you'll also want to add
observability to these components as they may be a point of failure.

In this documentation section, you find some recommendations on how to make them
observable.

Redis
=====

:ref:`Redis <installation_redis>` (or alternatively `Valkey <https://valkey.io/>`_) acts
as cache and message broker.

The `OTel Collector <https://opentelemetry.io/docs/collector/>`_ contrib package supports
extracting metrics from Redis instances through the
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
