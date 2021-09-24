.. _configuration_registration_objects:

===========
Objects API
===========

The `Objects API`_ allows us to easily store and expose various objects
according to the related objecttype resource in the Objecttypes API. Open Forms
supports create objects in the Objects API when used with a specific 
*objecttype*, the so-called `ProductAanvraag objecttype`_.

Open Forms can be configured to create an object of type ``ProductAanvraag`` to 
register form submissions.

Below is an example of the contents in the ``record.data`` attribute in the 
Objects API. The top-level has meta-data about the form submission, and the 
``data`` element holds the submitted form values:

.. tabs::

   .. group-tab:: Example

      .. code-block:: json

         {
           "data": {
              "naam": "Jan Jansen",
              "omschrijving": "Ik heb een vraag over mijn paspoort",
              "telefoonnummer": "0612345678"
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

1. In Open Forms, navigate to: **Configuration** > **Services**
2. Create a service for the Objects API (ORC) where the form data will be registered.

   a. Click **Service toevoegen**.
   b. Fill out the form:

      * **Label**: *Fill in a human readable label*, for example: ``My Objects API``
      * **Type**: Select the type: ``ORC``
      * **API root url**: The root of this API, *for example* ``https://example.com/objecten/api/v1/``

      * **Authorization type**: Select the option: ``API Key``
      * **Header key**: Fill in ``Authentication``
      * **Header value**: Fill in ``Token <tokenValue>`` where ``<tokenValue>`` is replaced by the token provided by the backend service
      * **OAS**: URL that points to the OAS, same URL as used for **API root url** with ``/schema/openapi.yaml`` added to it
        *for example:* ``https://example.com/objecten/api/v1/schema/openapi.yaml``

      * **NLX**: Support for NLX can be selected here if enabled in the installation
      * **User ID**: Audit trail user ID, usually same as the Client ID
      * **User representation**: *For example:* ``Open Forms``

   c. Click **Opslaan** and repeat to create configuration for the other component.

3. Create a second service, for the Documentregistratiecomponent (DRC) where the PDF summary and form attachment documents will be stored.

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

4. Navigate to **Configuration** > **Objects API configuration**
5. Enter the following details:

   * **Objects API**: Select the Objects API (ORC) service created above
   * **Documenten API**: Select the Documentregistratiecomponent (DRC) service created above
   * **Objecttype**: Fill in the default URL of the ProductAanvraag OBJECTTYPE in the Objecttypes API *For example* ``https://example.com/api/v1/objecttypes``
   * **Objecttype version**: Fill in the default version of the OBJECTTYPE in the Objecttypes API *For example:* ``1``
   * **Productaanvraag type**: Fill in the type of ProductAanvraag *For example:* ``terugbelnotitie``
   * **Submission report informatieobjecttype**: Fill in the default URL of the INFORMATIEOBJECTTYPE for the submission report in the Catalogi API *For example* ``https://example.com/api/v1/informatieobjecttypen/1/``
   * **Attachment informatieobjecttype**: Fill in the default URL of the INFORMATIEOBJECTTYPE for the submission attachments in the Catalogi API *For example* ``https://example.com/api/v1/informatieobjecttypen/2/``
   * **Organisatie RSIN**: Fill the RSIN to be referred to in the created objects. *For example:* ``123456789``


6. Click **Opslaan**

The Objects API configuration is now complete and can be selected as registration backend in the form builder.


.. _`Objects API`: https://objects-and-objecttypes-api.readthedocs.io/
.. _`ProductAanvraag objecttype`: https://github.com/open-objecten/objecttypes/tree/main/community-concepts/productaanvraag/