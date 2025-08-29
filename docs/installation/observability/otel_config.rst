.. _installation_observability_otel_config:

============================
Open Telemetry Configuration
============================

You should be able to use the standard Open Telemetry
`environment variables <https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/>`_,
but we highlight some that you'd commonly want to specify for typical use cases.

Disabling Open Telemetry
========================

Set ``OTEL_SDK_DISABLED=true`` to disable telemetry entirely. This does not affect the
(structured) logging to the container stdout/stderr.

Configuring the Open Telemetry sink
===================================

Enabling Open Telemetry (enabled by default) requires you to have a "sink" to push the
telemetry data to. Open Forms only supports the Open Telemetry Protocol (OTLP). You can
use any vendor that supports this protocol (over gRPC or HTTP/protobuf).

.. tip:: We recommend the usage of the Open Telemetry
   `Collector <https://opentelemetry.io/docs/collector/>`_ as sink - you are then in
   full control of how telemetry is processed and exported.

**Environment variables you likely want to set**

* ``OTEL_EXPORTER_OTLP_ENDPOINT``: network address where to send the metrics to. Examples
  are: ``https://otel.example.com:4318`` or ``http://otel-collector.namespace.cluster.svc:4317``.
  It defaults to ``localhost:4317``, which will **not** work in a container context.

* ``OTEL_EXPORTER_OTLP_METRICS_INSECURE``: set to ``true`` if the endoint is not protected
  with TLS.

* ``OTEL_EXPORTER_OTLP_HEADERS``: Any additional HTTP headers, e.g. when your collector
  is username/password protected with Basic auth, you want something like:
  ``Authorization=Basic <base64-username-colon-password>``.

* ``OTEL_EXPORTER_OTLP_PROTOCOL``: controls the wire protocol for the OTLP data. Defaults to
  ``grpc``. Available options: ``grpc`` and ``http/protobuf``.

* ``OTEL_METRIC_EXPORT_INTERVAL``: controls how often (in milliseconds) the metrics are
  exported. The exports run in a background thread and should not affect the performance
  of the application. The default is every minute (``60000``).

* ``_OTEL_ENABLE_CONTAINER_RESOURCE_DETECTOR=true``: enable this when not deploying on
  Kubernetes, but in another container runtime like Docker or Podman.

  .. tip:: On Kubernetes, use the Collector
     `attributes processor <https://opentelemetry.io/docs/platforms/kubernetes/collector/components/#kubernetes-attributes-processor>`_.
