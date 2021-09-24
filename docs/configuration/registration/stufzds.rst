.. _configuration_registration_stufzds:

========
StUF-ZDS
========

The StUF-ZDS (StUF Zaak- en Documentservices) is a SOAP based Zaak and 
Documents backend. Open Forms can be configured to access this SOAP-service to 
register form submissions.

.. note::

   This service contains sensitive data and requires a connection to a specific
   client system.

1. Obtain credentials and endpoint for StUF-ZDS from the client.
2. In Open Forms, navigate to: **Configuration** > **SOAP Services**
3. Click **Add SOAP Services** and fill in the following details:

   * **Label**: *Fill in a human readable label*, for example: ``My StUF-ZDS service``

4. In the **StUF parameters** section enter the receiving details provided by 
   the client. For the sending organiation details, you can fill in:

   * **Versturende applicatie**: Open Forms

5. In the **Connection** section:

   * **SOAP Version**: *Select the SOAP version of your backend provider*
   * **Endpoint BeantwoordVraag**: *Fill in the full URL to the endpoint for the SOAP 'BeantwoordVraag' action*
   * **Endpoint VrijeBerichten**: *Fill in the full URL to the endpoint for the SOAP 'VrijeBerichten' action*
   * **Endpoint OntvangAsynchroon**: *Fill in the full URL to the endpoint for the SOAP 'OntvangAsynchroon' action*

6. In the **Authentication** section:

   * **Security**: *select the security level required by your backend provider*

      * **Basic authentication**: use HTTP Basic authentication, requires to also fill in **Username** and **Password**
      * **SOAP extension: WS-Security**: use WS-Security, requires to also fill in **Username** and **Password**
      * **Both**: use both HTTP Basic authentication and WS-Security, requires to also fill in a shared **Username** and **Password**
      * **None**: no username/password based security (default)

    * **Certificate** and **Certificate key**: optionally provide a certificate and key file for client identification. If empty mutual TLS is disabled

7. Click **Save**
8. Navigate to **Configuration** > **StUF-ZDS configuration**
9. Select for the **Service**, the SOAP Service we created above
10. Fill the remaining fields with the desired values to be used to create the Zaak and related Documents in the selected StUF-ZDS backend.
11. Click **Save**

The StUF-ZDS configuration is now complete and can be selected as registration 
backend in the form builder.
