.. _configuration_registration_objects:

===========
Objects API
===========

The `Objects API`_ allows us to easily store and expose various objects
according to the related objecttype resource in the Objecttypes API. Open Forms
supports creating objects in the Objects API, such as the `ProductAanvraag objecttype`_.

Open Forms can be configured to create an object (of type ``ProductAanvraag``) to
register form submissions.

What does the Open Forms administator need?
===========================================

* API resource URL of object type(s) to use for registration. Open Forms does not (yet)
  need access to the Object Types API.
* Access the Objects API, with write permissions for the relevant object types. Open
  Forms creates and updates records.
* API resource URLs of document types (informatieobjecttype) in the Catalogi API -
  attachments are created using these document types:

    - PDF summary of submitted form data
    - CSV export of submitted form data (optional)
    - Attachments from uploads done by the end-user through ``file`` components.

* Write access to the Documenten API, some attachments/files are created there and then
  related to the record in the Objects API.

.. warning:: For forms with payment requirements, a PATCH request is made to the
   Objects API to update the payment status. This requires a version of the Objects API
   newer than 2.1.1, which is unreleased at the time of writing.

Configuration
=============

Below is an example of the contents in the ``record.data`` attribute in the
Objects API. The top-level has meta-data about the form submission, and the
``data`` element holds the submitted form values, nested within each step (using the step-slug as key):

.. tabs::

   .. group-tab:: Example

      .. code-block:: json

         {
           "data": {
             "uw-gegevens": {
               "naam": "Jan Jansen",
               "omschrijving": "Ik heb een vraag over mijn paspoort",
               "telefoonnummer": "0612345678"
             }
           },
           "type": "terugbelnotitie",
           "bsn": "111222333",
           "pdf_url": "https://example.com/documenten/api/v1/enkelvoudiginformatieobjecten/230bab4a-4b51-40c6-91b2-f2022008a7f8",
           "attachments": [],
           "submission_id": "a43e84ac-e08b-4d5f-8d5c-5874c6dddf56"
         }

   .. group-tab:: JSON-schema for Objecttype

      .. code-block:: json

         {
           "title": "ProductAanvraag",
           "default": {},
           "required": [
             "submission_id",
             "type",
             "data"
           ],
           "properties": {
             "data": {
               "$id": "#/properties/data",
               "type": "object",
               "title": "Object met de ingezonden formulierdata",
               "default": {},
               "examples": [
                 {
                   "field1": "value1"
                 }
               ]
             },
             "type": {
               "$id": "#/properties/type",
               "type": "string",
               "title": "Type productaanvraag",
               "default": "",
               "examples": [
                 "terugbelnotitie"
               ]
             },
             "bsn": {
               "$id": "#/properties/bsn",
               "type": "string",
               "title": "Burgerservicenummer",
               "default": "",
               "examples": [
                 "111222333"
               ]
             },
             "kvk": {
               "$id": "#/properties/kvk",
               "type": "string",
               "title": "KVK-nummer van het bedrijf in het Handelsregister",
               "default": "",
               "examples": [
                 "12345678"
               ]
             },
             "pdf_url": {
               "$id": "#/properties/pdf_url",
               "type": "string",
               "title": "URL van een document (in een Documenten API) dat de bevestigings PDF van Open Forms bevat",
               "format": "uri",
               "default": "",
               "examples": [
                 "https://example.com/documenten/api/v1/enkelvoudiginformatieobjecten/230bab4a-4b51-40c6-91b2-f2022008a7f8"
               ]
             },
             "csv_url": {
               "$id": "#/properties/csv_url",
               "type": "string",
               "title": "URL van een document (in een Documenten API) dat de CSV met ingezonden formulierdata bevat",
               "format": "uri",
               "default": "",
               "examples": [
                 "https://example.com/documenten/api/v1/enkelvoudiginformatieobjecten/aeaba696-4968-46a6-8b1e-016f503ed88d"
               ]
             },
             "attachments": {
               "$id": "#/properties/attachments",
               "type": "array",
               "items": {
                 "type": "string",
                 "format": "uri"
               },
               "title": "Lijst met URLs van de bijlagen van het ingezonden formulier in een Documenten API",
               "default": [],
               "examples": [
                 [
                   "https://example.com/documenten/api/v1/enkelvoudiginformatieobjecten/94ff43d6-0ee5-4b5c-8ed7-b86eaa908718"
                 ]
               ]
             },
             "submission_id": {
               "$id": "#/properties/submission_id",
               "type": "string",
               "title": "ID van de submission in Open Forms",
               "default": "",
               "examples": [
                 "a43e84ac-e08b-4d5f-8d5c-5874c6dddf56"
               ]
             },
             "additionalProperties": true
           }
         }


To configure the Objects API follow these steps:

#. In Open Forms, navigate to: **Configuration** > **Services**
#. Create a service for the Objects API (ORC) where the form data will be registered.

   a. Click **Service toevoegen**.
   b. Fill out the form:

      * **Label**: *Fill in a human readable label*, for example: ``My Objects API``
      * **Type**: Select the type: ``ORC``
      * **API root url**: The root of this API, *for example* ``https://example.com/objecten/api/v1/``

      * **Authorization type**: Select the option: ``API Key``
      * **Header key**: Fill in ``Authorization``
      * **Header value**: Fill in ``Token <tokenValue>`` where ``<tokenValue>`` is replaced by the token provided by the backend service
      * **OAS**: URL that points to the OAS, same URL as used for **API root url** with ``/schema/openapi.yaml`` added to it
        *for example:* ``https://example.com/objecten/api/v1/schema/openapi.yaml``

      * **NLX**: Support for NLX can be selected here if enabled in the installation
      * **User ID**: Audit trail user ID, usually same as the Client ID
      * **User representation**: *For example:* ``Open Forms``

   c. Click **Opslaan** and repeat to create configuration for the other component.

#. Create a second service, for the Documentregistratiecomponent (DRC) where the PDF summary and form attachment documents will be stored.

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

#. Create a third service, for the Zaaktypecatalogus (ZTC). This is needed to retrieve Informatieobjecttypen.

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

#. Navigate to **Configuration** > **Overview**. In the **Registration plugin** group, click on **Configuration** for the **Objects API registratie** line.
#. Enter the following details:

   * **Objects API**: Select the Objects API (ORC) service created above
   * **Documenten API**: Select the Documentregistratiecomponent (DRC) service created above
   * **Catalogi API**: Select the Zaaktypecatalogus (ZTC) service created above
   * **Objecttype**: Fill in the default URL of the ProductAanvraag OBJECTTYPE in the Objecttypes API *For example* ``https://example.com/api/v1/objecttypes``
   * **Objecttype version**: Fill in the default version of the OBJECTTYPE in the Objecttypes API *For example:* ``1``
   * **Productaanvraag type**: Fill in the type of ProductAanvraag *For example:* ``terugbelnotitie``
   * **Submission report informatieobjecttype**: Fill in the default URL of the INFORMATIEOBJECTTYPE for the submission report in the Catalogi API *For example* ``https://example.com/api/v1/informatieobjecttypen/1/``
   * **Upload submission CSV**: Indicate whether or not the submission CSV should be uploaded to the Documenten API by default (can be overridden per form)
   * **Submission report CSV informatieobjecttype**: Fill in the default URL of the INFORMATIEOBJECTTYPE for the submission report CSV in the Catalogi API *For example* ``https://example.com/api/v1/informatieobjecttypen/2/``
   * **Attachment informatieobjecttype**: Fill in the default URL of the INFORMATIEOBJECTTYPE for the submission attachments in the Catalogi API *For example* ``https://example.com/api/v1/informatieobjecttypen/3/``
   * **Organisatie RSIN**: Fill the RSIN to be referred to in the created objects. *For example:* ``123456789``
   * **JSON content template**: This is a template for the JSON that will be sent to the Object API nested in the
     ``record.data`` field.
   * **Payment status update JSON template**: This is a template for the JSON that will be sent with a PATCH request to
     the Object API to update the payment status of a submission. This JSON will be nested in the ``record.data.payment`` field.

#. Click **Opslaan**

The Objects API configuration is now complete and can be selected as registration backend in the form builder.

Technical
=========

Open Forms requires Objects API v2.2 or newer.

================  ==========================================
Objects API       Test status
================  ==========================================
2.2.x             Manually verified
2.3.x             Manually verified, integration tests in CI
================  ==========================================

.. _`Objects API`: https://objects-and-objecttypes-api.readthedocs.io/
.. _`ProductAanvraag objecttype`: https://github.com/open-objecten/objecttypes/tree/main/community-concepts/productaanvraag/
