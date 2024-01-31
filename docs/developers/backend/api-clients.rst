.. _developers_backend_api_clients:

===========
API clients
===========

Background
==========

Open Forms interfaces over HTTP with a bunch of third party APIs/services, for example
to:

* fetch :ref:`prefill data <configuration_prefill_index>`
* :ref:`register <configuration_registration_index>` submission data
* perform :ref:`service fetch <example_service_fetch>`

There are different flavours of interaction - JSON services (including REST), but also
SOAP (XML), StUF (SOAP/XML-based standard) and unknowns that the future may bring.

In the Dutch (local) government landscape, there are some common patterns in how you
connect with these services:

* mutual TLS (mTLS)
* basic auth credentials (username/password)
* API key
* Oauth2-based flows
* IP allowlists

Combinations of these patterns are possible too!

Open Forms uses an abstraction that accounts for these variations while allowing
developers to focus on the actual consuming of the service, packaged into the library
`ape-pie <https://ape-pie.readthedocs.io/en/latest/>`_.

Because it extends the core :mod:`requests` API, usage should feel familiar.

You are encouraged to define your own service-specific subclasses to modify behaviour
where needed.

.. _developers_backend_api_clients_factories:

Configuration factories
=======================

Configuration factories are a small abstraction that allow you to instantiate clients
with the appropriate configuration/presets from sources holding the configuration
details - for example database records.

Such a factory must implemented the :class:`ape_pie.ConfigAdapter` protocol.

Some examples that can serve as a reference:

* :class:`zgw_consumers.client.ServiceConfigAdapter`
* :class:`soap.client.session_factory.SessionFactory`
* :class:`stuf.service_client_factory.ServiceClientFactory`


Reference
=========

ZGW-consumers (JSON-based/RESTful services)
-------------------------------------------

See the `zgw-consumers`_ documentation.

.. _zgw-consumers: https://zgw-consumers.readthedocs.io/en/latest/

Zeep (SOAP client)
------------------

Zeep supports a ``session`` keyword argument for its transport, which is plug and play
with our base client.

.. automodule:: soap.client
    :members:

StUF (template based SOAP/XML)
------------------------------

.. automodule:: stuf.client
    :members:
