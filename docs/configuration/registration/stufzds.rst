.. _configuration_registration_stufzds:

========
StUF-ZDS
========

The StUF-ZDS (StUF Zaak- en Documentservices) is a SOAP based Zaak and Documents backend. Open Forms can be
configured to access this API to register form submissions.

1. In Open Forms, navigate to: **Configuration** > **Soap Services**
2. Click **Add Soap Services** and fill in the following details:

   * **Label**: *A human readable label*, for example: `StUF-ZDS registration`

3. In the **StUF parameters** section enter the sending and receiving organisation details provided by your backend provider
4. In the **Connection** section:

   * **SOAP Version**: select the SOAP version of your backend provider
   * **URL**: fill in the base URL of the SOAP service
   * **Endpoint BeantwoordVraag**: fill in the full URL to the endpoint for the SOAP 'BeantwoordVraag' action
   * **Endpoint VrijeBerichten**: fill in the full URL to the endpoint for the SOAP 'VrijeBerichten' action
   * **Endpoint OntvangAsynchroon**: fill in the full URL to the endpoint for the SOAP 'OntvangAsynchroon' action

5. In the **Authentication** section:

   * **Security**: select the security level required by your backend provider

      * **Basic authentication**: use HTTP Basic authentication, requires to also fill in **Username** and **Password**
      * **SOAP extension: WS-Security**: use WS-Security, requires to also fill in **Username** and **Password**
      * **Both**: use both HTTP Basic authentication and WS-Security, requires to also fill in a shared **Username** and **Password**
      * **None**: no username/password based security

    * **Certificate** and **Certificate key**: optionally provide a certificate and key file for client identification. If empty mutual TLS is disabled

6. Click **Save**
7. Navigate to **Configuration** > **StUF-ZDS configuration**
8. Select for the **Service**, the SOAP Service we created above
9. Fill the remaining fields with the desired values to be used to create the Zaak and related Documents in the selected StUF-ZDS backend.
10. Click **Save**

The StUF-ZDS configuration is now completed and can be selected as registration backend in the form builder.
