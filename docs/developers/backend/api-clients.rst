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
developers to focus on the actual consuming of the service.

API client base
===============

We have opted to implement a base API client class around the :class:`requests.Session`,
more specifically - a subclass of ``Session``.

Import it from:

.. code-block:: python

    from api_client import APIClient


It's a small extension of the requests ``Session``, allowing you to specify some session
defaults (such as mTLS and auth parameters) while requiring you to set a base URL. The
base URL prevents accidental sending of credentials to other URLs than the base, while
allowing you to implement clients using relative paths/URLs.

Because it extends the core :mod:`requests` API, usage should feel familiar.

You are encouraged to define your own service-specific subclasses to modify behaviour
where needed.

Recommended usage
-----------------

Our extension allows for configuring such an instance from "configuration objects",
whatever those may be:

.. code-block:: python

    from api_client import APIClient

    from .factories import my_factory

    client = APIClient.configure_from(my_factory)

    with client:
        # ⚡️ context manager -> uses connection pooling and is recommended!
        response1 = client.get("some-relative-path", params={"foo": ["bar"]})
        response2 = client.post("other-path", json={...})

The ``my_factory`` is a "special"
:ref:`configuration source <developers_backend_api_clients_factories>`, which feeds the
relevant initialization parameters to the :class:`api_client.client.APIClient` instance.

.. note:: You can (and should) use the client/session in a context manager to benefit
   from connection pooling and thus better performance when multiple requests are made.

Low level usage
---------------

The low level usage is essentially what is called by the factory usage. The biggest risk
is forgetting to apply certain connection configuration, like mTLS parameters, therefor
we recommend setting up a configuration factory instead.

.. code-block::

    from api_client import APIClient
    from requests.auth import

    # You can pass most attributes available on requests.Session, like auth/verify/cert...
    client = APIClient(
        "https://example.com/api/v1/",
        auth=HTTPBasicAuth("superuser", "letmein"),
        verify="/path/to/custom/ca-bundle.pem",
    )

    with client:
        # ⚡️ context manager -> uses connection pooling and is recommended!
        response1 = client.get("some-relative-path", params={"foo": ["bar"]})
        response2 = client.post("other-path", json={...})


.. _developers_backend_api_clients_factories:

Configuration factories
=======================

Configuration factories are a small abstraction that allow you to instantiate clients
with the appropriate configuration/presets from sources holding the configuration
details - for example database records.

Such a factory must implemented the ``APIClientFactory`` protocol:

.. autoclass:: api_client.typing.APIClientFactory
    :members:


Some examples that can serve as a reference:

* :class:`zgw_consumers_ext.api_client.ServiceClientFactory`
* :class:`soap.client.session_factory.SessionFactory`
* :class:`stuf.service_client_factory.ServiceClientFactory`


Reference
=========

ZGW-consumers (JSON-based/RESTful services)
-------------------------------------------

.. automodule:: zgw_consumers_ext.api_client
    :members:

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


Design constraints
------------------

The client implementation was set up with some design constraints:

- Must support the :class:`requests.Session` API
- Must be compatible with :class:`zgw_consumers.models.Service`,
  :class:`stuf.models.StUFService` and :class:`soap.models.SOAPService`
- Should encourage best practices (closing resources after use)
- Should not create problems when used with other libraries, e.g. ``requests-oauth2client``

Eventually we'd like to explore using ``httpx`` rather than ``requests`` - it has a
similar API, but it's also ``async`` / ``await`` capable. The abstraction of the
underlying driver (now requests, later httpx) should not matter and most importantly,
not be leaky.

.. note:: Not being leaky here means that you can use the requests API (in the future:
   httpx) like you would normally do without this library getting in the way.
