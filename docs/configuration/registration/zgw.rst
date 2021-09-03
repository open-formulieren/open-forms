.. _configuration_registration_zgw:

=======================
ZGW API's configuration
=======================

The ZGW (Zaak Gericht Werken) API's are a suite of REST based Zaak services. Open Forms can be
configured to access these API's to register form submissions.


1. In Open Forms, navigate to: **Configuration** > **Services**
2. Here we need to configure credentials for three related ZGW API's.

    - Zaakregistratiecomponent (ZRC)
    - Documentregistratiecomponent (DRC)
    - Zaaktypecatalogus (ZTC)

   These can be individual services or a hosted in a combined service like Open Zaak.

   a. Click **Service toevoegen**.
   b. Fill out the form for each of the three components:

      - **Label**: *For example:* ``Zaken``, ``Documenten`` or ``Zaaktypen``
      - **Type**: Select the type, one of: ``ZRC``, ``DRC`` or ``ZTC``
      - **API root url**: The root of this API, *for example* ``https://test.openzaak.nl/zaken/api/v1/``

      - **Client ID**: Fill the value provided by the backend service *For example:* ``open-zaak`` (*NOTE* this could be different for each component)
      - **Secret**: Fill the value provided by the backend service (*NOTE* this could be different for each component)
      - **Authorization type**: Select the option: ``ZGW client_id + secret``
      - **OAS**: URL that points to the OAS, same URL as used for **API root url** with ``/schema/openapi.yaml`` added to it
        *for example:* ``https://test.openzaak.nl/zaken/api/v1/schema/openapi.yaml``

      - **NLX**: Support for NLX can be selected here if enabled in the installation
      - **User ID**: Audit trail user ID, usually same as the Client ID
      - **User representation**: *For example:* ``Open Zaak``

   c. Click **Opslaan** and repeat to create configuration for the other components.


3. Navigate to **Configuration** > **ZGW API"s configuration**
4. Enter the following details:

   * **Zaken API:**: Select the Zaakregistratiecomponent (ZRC) service created above
   * **Documenten API:**: Select the Documentregistratiecomponent (DRC) service created above
   * **Catalogi API:**: Select the Zaaktypecatalogus (ZTC) service created above

5. Click **Opslaan en opnieuw bewerken** to save the form to retrieve the list of available types.
6. Continue entering the following details:

   * **Zaaktype**: Select the default Zaaktype to be used to create the Zaak.
   * **Informatieobjecttype**: Fill in the URL of the Informatieobjecttype to be used to create the Document.
   * **Organisatie RSIN**: Fill the RSIN to be referred to in the created objects.

7. Click **Opslaan**

The ZGW API's configuration is now completed.


