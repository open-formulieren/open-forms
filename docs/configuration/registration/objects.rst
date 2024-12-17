.. _configuration_registration_objects:

===========
Objects API
===========

The `Objects API`_ is a standard for generic storage of objects/records according to
your own, process-specific, data description, such as the `ProductAanvraag objecttype`_.

Open Forms supports registering form submisisons in the Objects API. The
:ref:`manual (Dutch) <manual_registration_objects_api>` describes how to configure a form
for usage with the Objects API.

What does the Open Forms administrator need?
============================================

* An instance of the `Objecttypes API`_ with:

    - an API token to access the API from Open Forms
    - one or more objecttypes (legacy configuration requires the API resource URL for
      these too)

* An instance of the `Objects API`_ (v2.2+) with:

    - (API) access to the above Objecttypes API
    - an API token to access the Objects API from Open Forms
    - write permissions for the relevant Objecttypes - Open Forms creates and updates
      records.

* An instance of the Catalogi API (e.g. via Open Zaak) with:

    - API credentials (client ID + secret) to read the available document types (
      informatieobjecttypen)
    - API resource URLs of the document type to use for the PDF summary of submitted
      form data
    - API resource URLs of the document type to use for the CSV of submitted form data
      (optional)
    - API resource URLs of the document type to use for the user uploaded attachments
      (optional, works as fallback). The document type can also be selected on each
      individual ``file`` component

* An instance of the Documenten API (e.g. via Open Zaak) with:

    - (API) access to the above Catalogi API
    - API credentials (client ID + secret) with write access to create documents of the
      document types mentioned above

Configuration
=============

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

#. Create a service for the Documenten API (DRC) where the PDF summary and form attachment documents will be stored.

   a. Click **Service toevoegen**.
   b. Fill out the form:

      * **Label**: *For example:* ``Documenten``
      * **Type**: Select the type: ``DRC``
      * **API root url**: The root of this API, *for example* ``https://example.com/documenten/api/v1/``

      * **Client ID**: Fill the value provided by the backend service *For example:* ``open-forms``
      * **Secret**: Fill the value provided by the backend service
      * **Authorization type**: Select the option: ``ZGW client_id + secret``
      * **OAS**: URL that points to the OAS, same URL as used for **API root url** with ``/schema/openapi.yaml`` added to it
        *for example:* ``https://example.com/documenten/api/v1/schema/openapi.yaml``

      * **NLX**: Support for NLX can be selected here if enabled in the installation
      * **User ID**: Audit trail user ID, usually same as the Client ID
      * **User representation**: *For example:* ``Open Forms``

#. Create a service for the Catalogi API (ZTC). This is needed to retrieve Informatieobjecttypen.

   a. Click **Service toevoegen**.
   b. Fill out the form:

      * **Label**: *For example:* ``Catalogi``
      * **Type**: Select the type: ``ZTC``
      * **API root url**: The root of this API, *for example* ``https://example.com/catalogi/api/v1/``

      * **Client ID**: Fill the value provided by the backend service *For example:* ``open-forms``
      * **Secret**: Fill the value provided by the backend service
      * **Authorization type**: Select the option: ``ZGW client_id + secret``
      * **OAS**: URL that points to the OAS, same URL as used for **API root url** with ``/schema/openapi.yaml`` added to it
        *for example:* ``https://example.com/catalogi/api/v1/schema/openapi.yaml``

      * **NLX**: Support for NLX can be selected here if enabled in the installation
      * **User ID**: Audit trail user ID, usually same as the Client ID
      * **User representation**: *For example:* ``Open Forms``

#. Navigate to **Configuration** > **Configuration overview**. In the
   **Registration plugins** group, click on **Manage API groups** for the
   **Objects API registratie** line.

#. Enter the following details:

   * **Name**: Enter a recognizable name, it will be displayed in various dropdowns.
   * **Objects API**: Select the Objects API (ORC) service created above
   * **Objecttypes API**: Select the Objecttypes API (ORC) service created above
   * **Documenten API**: Select the Documenten API (DRC) service created above
   * **Catalogi API**: Select the Zaaktypecatalogus (ZTC) service created above
   * **Organisatie RSIN**: Fill the RSIN to use as "bronorganisatie" in Document uploads.
     *For example:* ``123456789``. You an override this on a per-form basis.

   The following fields are deprecated - it's better to specify a catalogue and the
   description of the document types instead.

   * **Submission report informatieobjecttype**: Fill in the default URL of the
     INFORMATIEOBJECTTYPE for the submission report in the Catalogi API *For example*
     ``https://example.com/api/v1/informatieobjecttypen/1/``. You an override this on a
     per-form basis.
   * **Upload submission CSV**: Indicate whether or not the submission CSV should be
     uploaded to the Documenten API by default. You an override this on a per-form basis.
   * **Submission report CSV informatieobjecttype**: Fill in the default URL of the
     INFORMATIEOBJECTTYPE for the submission report CSV in the Catalogi API *For example*
     ``https://example.com/api/v1/informatieobjecttypen/2/``. You an override this on a
     per-form basis.
   * **Attachment informatieobjecttype**: Fill in the default URL of the
     INFORMATIEOBJECTTYPE for the submission attachments in the Catalogi API *For example*
     ``https://example.com/api/v1/informatieobjecttypen/3/``. You an override this on a
     per-form and per-file component basis.

   For the legacy configuration format, additional fields are available:

   * **Productaanvraag type**: Optionally fill in the default type of ProductAanvraag
     *For example:* ``terugbelnotitie``. You an override this on a per-form basis.
   * **JSON content template**: This is a template for the JSON that will be sent to the
     Objects API nested in the ``record.data`` field.
   * **Payment status update JSON template**: This is a template for the JSON that will
     be sent with a PATCH request to the Object API to update the payment status of a
     submission. This JSON will be merge-patched in the ``record.data`` field.

#. Click **Opslaan**

The Objects API configuration is now complete and can be selected as registration backend in the form builder.
When doing so, the corresponding objecttype and objecttype version will have to be configured.

.. versionchanged:: 2.6.0

   The objecttype URL and version must be configured at the form level, and can no
   longer be configured globally.

.. _configuration_registration_objects_objecttype_tips:

Recommendations for the Objecttype JSON Schemas
===============================================

The objecttype definition uses `JSON Schema <https://json-schema.org/>`_, and this schema
is processed by Open Forms.

There are some pitfalls with JSON Schema that can lead to unexpected results, so we have
some guidelines for schema authors:


* Preferably, define the ``$schema`` property pointing to the version of the
  specification you are using. If not specified, Open Forms will assume the latest
  specification (*2020-12*) applies, which may not be compatible.

* Do not omit the ``type`` property for the top-level object. In practice, this should
  probably always be set to the value ``"object"``. If unspecified, technically any
  data type is allowed which is probably not what you intended.

* Include ``additionalProperties: false`` for objects - the default is that any
  unspecified, additional properties are allowed and those cannot be input-validated.

* Using references (``$ref: #/foo``) is supported, but they should not (yet) point to an
  external entity (resolving this will likely be added in the future in a way that does
  not create security issues).

.. _configuration_registration_objects_feature_flags:

Feature flags
=============

Feature flags can be enabled or disabled in the admin interface, via **Admin** >
**Configuration** > **Flag states**.

``ZGW_APIS_INCLUDE_DRAFTS``
---------------------------

When drafts are included in the ZGW APIs integration, you will be able to select
document types that have not been published yet for the attachments, submission report
PDF and CSV. This can be useful when you're testing out things and iterating quickly.

.. note:: Support for creating documents from unpublished document types depends on your
   particular ZGW API's provider/implementation. The VNG standard requires document
   types to be published before you can create documents of that type.

Can be enabled at :ref:`deploy time <installation_environment_config_feature_flags>` or
through the admin interface. Find or create the record with:

* **Flag**: ``ZGW_APIS_INCLUDE_DRAFTS``
* **Condition name**: ``boolean``
* **Expected value**: ``true`` to enable it, ``false`` to disable.
* **Required**: leave unchecked

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

.. versionchanged:: 2.6.0

    Objects API versions older than 2.2.0 are no longer officially supported. You need
    at least version 2.2.0.

================  ===============================================
Objecttypes API   Test status
================  ===============================================
2.0.x             Unknown
2.1.x             Manually verified
2.2.x             Manually verified, automated end-to-end testing
================  ===============================================

For Documents API integration (to upload attachments), Open Forms requires the
Catalogi API and Documenten API.

================  ===============================================
Catalogi API      Test status
================  ===============================================
1.0.x             Manually verified, some tests in CI
1.1.x             Manually verified, some tests in CI
1.2.x             Manually verified, some tests in CI
1.3.x             Manually verified, automated end-to-end testing
================  ===============================================

================  ===============================================
Documenten API    Test status
================  ===============================================
1.0.x             Manually verified, some tests in CI
1.1.x             Manually verified, some tests in CI
1.2.x             Manually verified, some tests in CI
1.3.x             Manually verified, some tests in CI
1.4.x             Manually verified, automated end-to-end testing
================  ===============================================


.. _`Objects API`: https://objects-and-objecttypes-api.readthedocs.io/
.. _`Objecttypes API`: https://objects-and-objecttypes-api.readthedocs.io/en/latest/#objecttypes-api
.. _`ProductAanvraag objecttype`: https://github.com/open-objecten/objecttypes/tree/main/community-concepts/productaanvraag/
