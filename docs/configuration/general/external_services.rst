.. _configuration_general_external_services:

=================
External services
=================

Open Forms can write and read information to and from external systems. This is great
when you need to integrate with existing (JSON) APIs, SOAP webservices or HTTP endpoints
in general.

The connection parameters to these services are configurable in the admin interface,
provided you have administrator permissions (typically this would be a different role
than the people creating/managing forms).

.. note:: If you got to this page via the manual and don't have permissions
   to manage services, please contact your functional administrator.

.. _configuration_general_external_services_api_services:

(API) services
==============

We group services that (mostly) talk JSON under the (API) services. While they can be
used for data in formats other than JSON, they are generally simpler to use and
configure compared to SOAP and/or StUF-based services.

Examples of this type of services are:

* the ZGW API's
* the Objects API
* Haal Centraal services (BRP personen bevragen, KVK, Kadaster...)

To configure such a service, you need to have:

* the base URL where the service is hosted
* credentials (if relevant), like an API key or client ID/secret

Configuring a service
---------------------

#. In the admin interface, navigate to **Configuration** > **Services**.

#. Click **Add a service** to bring up the configuration form.

#. Fill out the form fields:

    * **Label**: provide a recognizable label. This will be displayed in dropdowns to
      select a service.

    * Either enter the URL to the OpenAPI specification or upload a file. For *most*
      services you can use a :ref:`dummy OAS <dummy_oas>` since these fields have become
      obsolete (and will be removed in a future update).

    * **Type**: Select the appropriate type or if none is relevant, select ``ORC (Overige)``.

    * **API root URL**: the base URL where the API is hosted. All API endpoints will be
      added relative to this. For example: ``https://example.com/api/``.

    * **Client ID** and **Secret** - these are only relevant when the **Authorization type**
      is set to ``ZGW client_id + secret``.

    * **Header key** the header name for the API credential when the **Authorization type**
      is set to ``API key``. Examples are: ``Authorization`` or ``X-API-Key`` - the value
      depends on your API provider.

    * **Header value** the API credential when the **Authorization type**
      is set to ``API key``. The exact value and format depends on your API provider.
      Some examples are: ``Token <api key>`` or just plainly
      ``e2c98134-3dc8-4134-88fc-aec604bf8394``.

    * If mutual TLS or particular server certificates are involved (typically
      certificate chains signed by the G1 root), you can manage these through the
      **Client certificate** and **Server certificate** fields. See also our support
      for :ref:`self-signed certificates <installation_self_signed>` in the installation
      documentation.

    * The remaining form fields can be left blank.

#. Click **Save** to persist the configuration.

.. _dummy_oas:

.. code-block:: yaml
    :caption: Dummy OAS

    version: 3.0.0
    info:
      title: Dummy
      version: 1.0.0
    paths: {}

SOAP (and StUF) services
========================

.. note:: StUF services requires a SOAP service to be configured as they are a layer on
   top of SOAP.

Configuring a SOAP service
--------------------------

#. In the admin interface, navigate to **Configuration** > **SOAP services**.

#. Click **Add a SOAP service** to bring up the configuration form.

#. Fill out the form fields:

    * **Label**: provide a recognizable label. This will be displayed in dropdowns to
      select a service.

    * **URL**: if you're defining a StUF-service, this field can be left blank because
      the StUF endpoints are defined elsewhere. Otherwise, you must specify the URL
      where SOAP messages are sent to.

    * If mutual TLS or particular server certificates are involved (typically
      certificate chains signed by the G1 root), you can manage these through the
      **Client certificate** and **Server certificate** fields. See also our support
      for :ref:`self-signed certificates <installation_self_signed>` in the installation
      documentation.

    * The remaining form fields are optional and configuration depends on the particular
      service you're connecting with.

#. Click **Save** to persist the configuration.
