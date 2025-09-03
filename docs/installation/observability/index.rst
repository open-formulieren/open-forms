.. _installation_observability_index:

=============
Observability
=============

Observability is an umbrella term for a number of principles and technologies to get
insight in running (distributed) systems. It typically focuses on Metrics, Logging and
Tracing, which provide insight in:

* what the application is doing, in particular as part of a larger system, such as
  microservice environments
* performance of the system
* how the system is used

Open Forms operates in distributed environments, and being able to fully trace a
customer request from start to end, observability tools are crucial. Below we provide
some additional context for infastructure teams that wish to integrate Open Forms in
their observability stack.

.. versionadded:: 3.2.0

    Open Forms is being fitted with better instrumentation to facilitate vendor-agnostic
    observability.

.. toctree::
   :maxdepth: 1
   :caption: Contents

   logging
   metrics
   tracing
   error_monitoring
   otel_config
   supporting_components

.. seealso:: The base integration layer is provided through our shared library, which
   includes some `architecture documentation <https://maykin-django-common.readthedocs.io/en/latest/otel.html#architecture>`_.
