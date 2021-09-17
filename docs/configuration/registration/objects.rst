.. _configuration_registration_objects:

============
Objecten API
============

The Objecten API is a suite of REST based object registration services. Open Forms can be
configured to access these API's to register form submissions.

Below an example of the registration in the Objects API, where the top-level has meta-data about the form submission, and the ``data`` element holds the submitted form values:

.. code-block:: json

    {
        "data": {
             "naam": "Jan Jansen",
             "omschrijving": "Ik heb een vraag over mijn paspoort",
             "telefoonnummer": "0612345678"
        },
        "type": "terugbelnotitie",
        "bsn": "111222333",
        "pdf_url": "https://openzaak.nl/documenten/api/v1/enkelvoudiginformatieobjecten/230bab4a-4b51-40c6-91b2-f2022008a7f8",
        "attachments": [],
        "submission_id": "a43e84ac-e08b-4d5f-8d5c-5874c6dddf56"
    }

To configure the Objecten API follow these steps:

1. In Open Forms, navigate to: **Configuration** > **Services**
2. Create a service for the Objecten API (ORC) where the form data will be registered.

   a. Click **Service toevoegen**.
   b. Fill out the form:

      * **Label**: *For example:* ``Objecten``
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

4. Navigate to **Configuration** > **Objecten API configuration**
5. Enter the following details:

   * **Objects API**: Select the Objecten API (ORC) service created above
   * **Documenten API**: Select the Documentregistratiecomponent (DRC) service created above
   * **Objecttype**: Fill in the default URL of the ProductAanvraag OBJECTTYPE in the Objecttypes API *For example* ``https://example.com/api/v1/objecttypes``
   * **Objecttype version**: Fill in the default version of the OBJECTTYPE in the Objecttypes API *For example:* ``1``
   * **Productaanvraag type**: Fill in the type of ProductAanvraag *For example:* ``terugbelnotitie``
   * **Submission report informatieobjecttype**: Fill in the default URL of the INFORMATIEOBJECTTYPE for the submission report in the Catalogi API *For example* ``https://example.com/api/v1/informatieobjecttypen/1/``
   * **Attachment informatieobjecttype**: Fill in the default URL of the INFORMATIEOBJECTTYPE for the submission attachments in the Catalogi API *For example* ``https://example.com/api/v1/informatieobjecttypen/2/``
   * **Organisatie RSIN**: Fill the RSIN to be referred to in the created objects. *For example:* ``123456789``


6. Click **Opslaan**

The Objecten API configuration is now completed and can be selected as registration backend in the form builder.

