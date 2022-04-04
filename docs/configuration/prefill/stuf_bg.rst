.. _configuration_prefill_stuf_bg:

=======
StUF-BG
=======

`StUF-BG`_ (StUF Basis Gegegevens) is a message standard that allows retrieving
of personal information through a SOAP service from municipalities and
government organisations. Open Forms can be configured to use this service to
prefill personal data of the person filling out the form.

.. _`StUF-BG`: https://www.gemmaonline.nl/index.php/Sectormodel_Basisgegevens:_StUF-BG

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
**Security**
Public certificate            The certificate, used by the service, to identify itself for 2-way TLS.
**SOAP services**
BeantwoordVraag endpoint      URL for the ``BeantwoordVraag`` SOAP-endpoint that Open Forms can access.
**Stuurgegevens**
Ontvanger Organisatie         Name of the organization submissions are sent to.
Ontvanger Applicatie          Name of the application submissions are sent to.
============================  =======================================================================================


What does the service provider need?
====================================

The values for these parameters should be provided to the service provider by
the Open Forms administrator.

============================  =======================================================================================
Parameter                     Description
============================  =======================================================================================
**Security**
Public certificate            The certificate, used by Open Forms, to identify itself for 2-way TLS.
IP address                    The IP address of the Open Forms server (optional, for whitelisting).
**Stuurgegevens**
Zender Organisatie            Typically the organization name but can be whatever the service provider configured.
Zender Applicatie             Typically ``Open Forms`` but can be whatever the service provider configured.
============================  =======================================================================================


Configuration
=============

1. Obtain credentials and endpoint for StUF-ZDS from the client.
2. In Open Forms, navigate to: **Configuration** > **SOAP Service**
3. Click **Add SOAP Service** and fill in the following details:

   * **Label**: *Fill in a human readable label*, for example: ``My StUF-BG service``
   * **URL**: *Fill in the full URL to the endpoint for the SOAP 'BeantwoordVraag' action*
   * **SOAP Version**: *Select the SOAP version of the client system. Typically,
     this is verison 1.1.*

4. In the **Authentication** section:

   * **Security**: *Select the security level required by your backend provider*

      * **Basic authentication**: use HTTP Basic authentication, requires to also fill in **Username** and **Password**
      * **SOAP extension: WS-Security**: use WS-Security, requires to also fill in **Username** and **Password**
      * **Both**: use both HTTP Basic authentication and WS-Security, requires to also fill in a shared **Username** and **Password**
      * **None**: no username/password based security (default)

   * **Gebruiker** / **wachtwoord**
   * **Client Certificate**: optionally provide a certificate and key file that Open Forms will use to identify itself to the server. If empty mutual TLS is disabled.
   * **Server Certificate**: optionally provide a certificate to check the certificate provided by the server. If empty, the value of the environment variable ``REQUESTS_CA_BUNDLE`` is used to retrieve the list of trusted certificates.

7. Click **Save**
8. Navigate to **Configuration** > **Configuration Overview**. In the **Prefill plugin** group, click on **Configuration** for the **StUF-BG** line.
9.  Click on the 'plus' icon next to the drop down.
10. Fill in the following details:

   * **Soap service**: select the soap service that was created above.
   * **Versturende applicatie**: Open Forms
   * **Ontvangende applicatie**: Name of the application submissions are sent to.
   * **Endpoint BeantwoordVraag**: *Fill in the same as the URL field used in the SOAP service above*

11. Click **Save**
12. When back on the **StUF-BG** page, refresh the page and select the StUf-BG service that was just created.
13. Click **Save**

The StUF-BG configuration is now completed.


Technical
=========

================  ===================
Service           Supported versions
================  ===================
StUF-BG           3.10  (``npsLv01``)
================  ===================
