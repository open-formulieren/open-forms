.. _configuration_registration_zgw:

=========
ZGW API's
=========

The `ZGW (Zaakgericht Werken) API's`_ are a suite of REST based Zaak services.
Open Forms can be configured to access these API's to register form submissions.

.. _`ZGW (Zaakgericht Werken) API's`: https://vng-realisatie.github.io/gemma-zaken/standaard/

.. note::

   This service contains sensitive data and requires a connection to an
   external system, offered or maintained by a service provider.


What does the Open Forms administrator need?
============================================

The values for these parameters should be provided to the Open Forms
administrator by the service provider.

============================  =======================================================================================
Parameter                     Description
============================  =======================================================================================
**Catalogi API**
API root URL                  Root URL for the Catalogi API that Open Forms can access.
Client ID                     Client ID for the JWT-token.
Secret                        Secret for the JWT-token.
**Zaken API**
API root URL                  Root URL for the Zaken API that Open Forms can access.
Client ID                     Client ID for the JWT-token.
Secret                        Secret for the JWT-token.
**Documenten API**
API root URL                  Root URL for the Documenten API (version 1.1+) that Open Forms can access.
Client ID                     Client ID for the JWT-token.
Secret                        Secret for the JWT-token.
**ZGW API's**
Organisatie RSIN              The RSIN for the organization configured in the service
============================  =======================================================================================


What does the service provider need?
====================================

The values for these parameters should be provided to the service provider by
the Open Forms administrator.

============================  =======================================================================================
Parameter                     Description
============================  =======================================================================================
**Security**
IP address                    The IP address of the Open Forms server (optional, for whitelisting).
============================  =======================================================================================


Configuration
=============

#. In Open Forms, navigate to: **Configuration** > **Services**
#. Here we need to configure credentials for three related ZGW API's:

    - Zaakregistratiecomponent (ZRC)
    - Documentregistratiecomponent (DRC)
    - Zaaktypecatalogus (ZTC)

   These can be individual services or a hosted in a combined service like Open Zaak.

   a. Click **Service toevoegen**.
   b. Fill out the form for each of the three components:

      * **Label**: *Fill in a human readable label*, for example: ``My Zaken API``, ``My Documenten API`` or ``My Zaaktypen API``
      * **Type**: Select the type, one of: ``ZRC``, ``DRC`` or ``ZTC``
      * **API root url**: The root of this API, *For example* ``https://example.com/zaken/api/v1/``

      * **Client ID**: Fill the value provided by the backend service. *For example:* ``open-zaak`` (*NOTE* this could be different for each component)
      * **Secret**: Fill the value provided by the backend service (*NOTE* this could be different for each component)
      * **Authorization type**: Select the option: ``ZGW client_id + secret``
      * **OAS**: URL that points to the OAS, same URL as used for **API root url** with ``/schema/openapi.yaml`` added to it.
        *For example:* ``https://example.com/zaken/api/v1/schema/openapi.yaml``

      * **NLX**: Support for NLX can be selected here if enabled in the installation
      * **User ID**: Audit trail user ID, usually same as the Client ID
      * **User representation**: *For example:* ``Open Forms``

   c. Click **Opslaan** and repeat to create configuration for the other components.


#. Navigate to **Configuration** > **Overview**. In the **Registration plugin** group, click on **Configuration** for the **ZGW API's** line.
#. Click on ``Add a ZGW API set``.
#. Enter the following details:

   * **Zaken API**: Select the Zaakregistratiecomponent (ZRC) service created above
   * **Documenten API**: Select the Documentregistratiecomponent (DRC) service created above
   * **Catalogi API**: Select the Zaaktypecatalogus (ZTC) service created above

#. Click **Opslaan en opnieuw bewerken** to save the form to retrieve the list of available types.
#. Continue entering the following details:

   * **Organisatie RSIN**: Fill the RSIN to be referred to in the created objects. *For example:* ``123456789``

#. You can combine ZGW API with Objects API. A default JSON content template is provided.

#. Click **Opslaan**

The ZGW API's configuration is now completed and can be selected as registration backend
in the form builder. At the form level, you must specify some more configuration
parameters, such as the catalogue, case type and document type to use. Additional
optional fields are available too - see the :ref:`user manual <manual_registration_zgw_apis>`.

Technical
=========

================  ===================
API               Supported versions
================  ===================
Zaken API         1.0+
Documenten API    1.1+
Catalogi API      1.0+
================  ===================
