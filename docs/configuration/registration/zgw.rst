.. _configuration_registration_zgw:

=========
ZGW API's
=========

The `ZGW (Zaakgericht Werken) API's`_ are a suite of REST based Zaak services.
Open Forms can be configured to access these API's to register form submissions.

.. _`ZGW (Zaakgericht Werken) API's`: https://vng.nl/projecten/zaakgericht-werken-api

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
OAS                           URL to the OAS.
Client ID                     Client ID for the JWT-token.
Secret                        Secret for the JWT-token.
**Zaken API**
API root URL                  Root URL for the Zaken API that Open Forms can access.
OAS                           URL to the OAS.
Client ID                     Client ID for the JWT-token.
Secret                        Secret for the JWT-token.
**Documenten API**
API root URL                  Root URL for the Documenten API (version 1.1+) that Open Forms can access.
OAS                           URL to the OAS.
Client ID                     Client ID for the JWT-token.
Secret                        Secret for the JWT-token.
**ZGW API's**
Zaaktype identificatie        Identification of the (default) zaaktype.
Informatieobjecttype URL      Full URL the documenttype resource in the Catalogi API, used for the submission PDF.
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

   * **Zaaktype**: Select the default Zaaktype to be used to create the Zaak. *For example:* ``https://example.com/catalogi/api/v1/zaaktypen/1/``
   * **Informatieobjecttype**: Fill in the URL of the Informatieobjecttype to be used to create the Document. *For example:* ``https://example.com/catalogi/api/v1/informatieobjecttypen/1/``
   * **Organisatie RSIN**: Fill the RSIN to be referred to in the created objects. *For example:* ``123456789``

#. You can combine ZGW API with Objects API. The submission data will be sent to both if the following have been provided:

   * **Objects API - Objecttype**: Fill in the default URL of the ProductAanvraag OBJECTTYPE in the Objecttypes API. *For example* ``https://example.com/api/v1/objecttypes``
   * **Objects API - Objecttype version**: Fill in the default version of the OBJECTTYPE in the Objecttypes API. *For example:* ``1``

#. You can map a form variable with a Zaak property (eigenschap) by clicking the related button (*Map variables to case properties*). 
   A modal will open where you have to choose the variable along with providing a valid property name. Both fields must be provided in order to create a mapping.

#. Click **Opslaan**

If you have added services to multiple ZGW APIs, you can create multiple ZGW API sets. This will enable you to specify
different ZGW API sets on a form. If you do not specify a ZGW API set on the form, then a default set will be used. The
default can be configured as follows:

#. Navigate to **Miscellaneous** > **ZGW APIs configuration**.
#. Select the desired default set.
#. Save the form.

The ZGW API's configuration is now completed and can be selected as registration backend in the form builder.
In each form, the global defaults can be overwritten and additional properties can be configured. These include:

   * **Vertrouwelijkheidaanduiding**: The level of confidentiality of the case.
   * **Medewerker roltype**: The description (omschrijving) of the Roltype associated to the Zaaktype to be used
     when creating a role for an employee filling in a form for a citizen or company.
     For example: ``some description``.


Technical
=========

================  ===================
API               Supported versions
================  ===================
Zaken API         1.0
Documenten API    1.1+
Catalogi API      1.0
================  ===================
