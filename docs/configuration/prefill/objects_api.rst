.. _configuration_prefill_objects_api:

===========
Objects API
===========

*This plugin is also known as the "product prefill" feature.*

The `Objects API`_ stores data records of which the structure and shape are defined by a
particular object type definition in the `Objecttypes API`_. These records can be used
to pre-fill form fields if an object reference is passed when the form is started.

.. note::

   The service likely contains sensitive data. It is required to use authentication on
   the form, as this information is used to test ownership of the referenced object.

What does the Open Forms administrator need?
============================================

* An instance of the `Objecttypes API`_ with:

    - an API token to access the API from Open Forms
    - one or more objecttypes

* An instance of the `Objects API`_ (v2.2+) with:

    - (API) access to the above Objecttypes API
    - an API token to access the Objects API from Open Forms
    - read permissions for the relevant Objecttypes - Open Forms reads records.

Configuration
=============

Configuration is similar to :ref:`its registration counterpart <configuration_registration_objects>`,
but only the objecttypes and objects services are required.

.. tip:: You can re-use the same API groups that are used for the registration plugin.

To configure the Objects API follow these steps:

#. In Open Forms, navigate to: **Configuration** > **Services**
#. Create a service for the Objects API (ORC) where the form data will be registered.

   a. Click **Service toevoegen**.
   b. Fill out the form:

      * **Label**: *Fill in a human readable label*, for example: ``My Objects API``
      * **Type**: Select the type: ``ORC``
      * **API root url**: The root of this API, *for example* ``https://example.com/objecten/api/v2/``

      * **Authorization type**: Select the option: ``API Key``
      * **Header key**: Fill in ``Authorization``
      * **Header value**: Fill in ``Token <tokenValue>`` where ``<tokenValue>`` is replaced by the token provided by the backend service
      * **OAS**: URL that points to the OAS, same URL as used for **API root url** with ``/schema/openapi.yaml`` added to it
        *for example:* ``https://example.com/objecten/api/v1/schema/openapi.yaml``

      * **NLX**: Support for NLX can be selected here if enabled in the installation

   c. Click **Opslaan** and repeat to create configuration for the other component.

#. Create a service for the Objecttypes API (ORC).

   a. Click **Service toevoegen**.
   b. Fill out the form:

      * **Label**: *Fill in a human readable label*, for example: ``My Objecttypes API``
      * **Type**: Select the type: ``ORC``
      * **API root url**: The root of this API, *for example* ``https://example.com/objecttypen/api/v2/``

      * **Authorization type**: Select the option: ``API Key``
      * **Header key**: Fill in ``Authorization``
      * **Header value**: Fill in ``Token <tokenValue>`` where ``<tokenValue>`` is replaced by the token provided by the backend service
      * **OAS**: URL that points to the OAS, same URL as used for **API root url** with ``/schema/openapi.yaml`` added to it
        *for example:* ``https://example.com/objecttypen/api/v1/schema/openapi.yaml``

      * **NLX**: Support for NLX can be selected here if enabled in the installation

   c. Click **Opslaan** and repeat to create configuration for the other component.

#. Navigate to **Configuration** > **Configuration overview**. In the
   **Prefill plugins** group, click on **Manage API groups** for the **Objects API** line.

#. Enter the following details:

    * **Name**: Enter a recognizable name, it will be displayed in various dropdowns.
    * **Objects API**: Select the Objects API (ORC) service created above
    * **Objecttypes API**: Select the Objecttypes API (ORC) service created above

   The remainder of the fields can be left empty.

#. Click **Save**

The Objects API configuration is now complete and can be selected as prefill backend in
the form builder. When doing so, you will be able to select the desired object type and
its version.

Recommendations for the Objecttype JSON Schemas
===============================================

The same recommendations apply as for the
:ref:`registration plugin <configuration_registration_objects_objecttype_tips>`. We
rely heavily on the JSON Schema specified in the object type.

Technical
=========

Open Forms requires Objects API v2.2 or newer and the Objecttypes API v2.0 or newer.

================  ===============================================
Objects API       Test status
================  ===============================================
2.2.x             Manually verified
2.3.x             Manually verified
2.4.x             Manually verified, automated end-to-end testing
================  ===============================================

================  ===============================================
Objecttypes API   Test status
================  ===============================================
2.0.x             Unknown
2.1.x             Manually verified
2.2.x             Manually verified, automated end-to-end testing
================  ===============================================

.. _`Objects API`: https://objects-and-objecttypes-api.readthedocs.io/en/latest/
.. _`Objecttypes API`: https://objects-and-objecttypes-api.readthedocs.io/en/latest/
