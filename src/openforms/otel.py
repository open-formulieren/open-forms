"""
Manage the OpenTelemetry SDK initialization.

.. todo:: once stable-ish, move to maykin-common.
"""

from typing import Literal, assert_never
from uuid import uuid4

from django.conf import settings

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_INSTANCE_ID, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

__all__ = [
    "setup_otel",
]

_OTEL_INITIALIZED = False

type ExportProtocol = Literal["gRPC", "http"]


def setup_otel() -> None:
    """
    Initialize the open telemetry SDK.

    The bulk of the configuration is taken from the environment automatically by the
    OTEL SDK.

    .. note:: Before calling this, ensure that the right Django settings are loaded.

    .. note:: The SDK may only be initialized once. When using celery and/or runserver
       with autoreload, this entrypoint may be called multiple times so we guard against
       this with a global.
    """

    global _OTEL_INITIALIZED
    if _OTEL_INITIALIZED:
        return

    # service name is guaranteed to be set through envvars
    resource = Resource.create(
        attributes={
            SERVICE_VERSION: settings.RELEASE,
            SERVICE_INSTANCE_ID: str(uuid4()),
        }
    )

    OTLPMetricExporter, OTLPSpanExporter = load_exporters(settings.OF_OTEL_PROTOCOL)

    tracer_provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter())
    tracer_provider.add_span_processor(processor)
    trace.set_tracer_provider(tracer_provider)

    reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    _OTEL_INITIALIZED = True


def load_exporters(protocol: ExportProtocol):
    match protocol:
        case "gRPC":
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                OTLPMetricExporter,
            )
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            return (OTLPMetricExporter, OTLPSpanExporter)
        case "http":
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
                OTLPMetricExporter,
            )
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            return (OTLPMetricExporter, OTLPSpanExporter)
        case _:  # pragma: no cover
            assert_never(protocol)
