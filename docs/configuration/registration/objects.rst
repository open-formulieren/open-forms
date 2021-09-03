.. _configuration_registration_objects:

==========================
Objecten API configuration
==========================

The Objecten API is a suite of REST based object registration services. Open Forms can be
configured to access these API's to register form submissions.

1. In Open Forms, navigate to: **Configuration** > **Services**
2. Here we need to configure credentials for two related API's.

    - Objecten API (ORC)
    - Documentregistratiecomponent (DRC)

   a. Click **Service toevoegen**.
   b. Fill out the form for each of the two components:

      * **Label**: *For example:* ``Objecten`` or ``Documenten``
      * **Type**: Select the type, one of: ``ORC`` or ``DRC``
      * **API root url**: The root of this API, *for example* ``https://test.openzaak.nl/objecten/api/v1/``

      * **Client ID**: Fill the value provided by the backend service *For example:* ``open-zaak`` (*NOTE* this could be different for each component)
      * **Secret**: Fill the value provided by the backend service (*NOTE* this could be different for each component)
      * **Authorization type**: Select the option: ``ZGW client_id + secret``
      * **OAS**: URL that points to the OAS, same URL as used for **API root url** with ``/schema/openapi.yaml`` added to it
        *for example:* ``https://test.openzaak.nl/objecten/api/v1/schema/openapi.yaml``

      * **NLX**: Support for NLX can be selected here if enabled in the installation
      * **User ID**: Audit trail user ID, usually same as the Client ID
      * **User representation**: *For example:* ``Open Forms``

   c. Click **Opslaan** and repeat to create configuration for the other component.


3. Navigate to **Configuration** > **Objecten API configuration**
4. Enter the following details:

   * **Objects API**: Select the Objecten API (ORC) service created above
   * **Documenten API**: Select the Documentregistratiecomponent (DRC) service created above
   * **Objecttype:**: Fill in the default URL of the ProductAanvraag OBJECTTYPE in the Objecttypes API
   * **Objecttype version**: Fill in the default version of the OBJECTTYPE in the Objecttypes API
   * **Productaanvraag type**: Fill in the type of ProductAanvraag
   * **Submission report informatieobjecttype**: Fill in the default URL of the INFORMATIEOBJECTTYPE for the submission report in the Catalogi API
   * **Attachment informatieobjecttype**: Fill in the default URL of the INFORMATIEOBJECTTYPE for the submission attachments in the Catalogi API
   * **Organisatie RSIN**: Fill the RSIN to be referred to in the created objects.


5. Click **Opslaan**

The Objecten API configuration is now completed and can be selected as registration backend in the form builder.

