.. _configuration_registration_msgraph:

=====================================
Microsoft Graph (OneDrive/Sharepoint)
=====================================

`Microsoft Graph`_ is a suite of REST based API's that connects with various Microsoft services like Azure, Office365 and Sharepoint.
Open Forms can be configured to access these API's to register form submissions.

.. _`Microsoft Graph`: https://docs.microsoft.com/en-us/graph/overview


.. note::

   This service contains sensitive data and requires a connection to an
   external system, offered or maintained by a service provider.


What does the Open Forms administrator need?
============================================

This registration backend requires a Microsoft Azure application.
These can be registered and managed in the `Azure App Registrations`_ portal.

Note this plugin authenticates using the application identity (eg: *Oath client credentials grant flow*) and doesn't support *Microsoft Personal accounts* accounts.


.. _`Azure App Registrations`: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade

============================  =======================================================================================
Parameter                     Description
============================  =======================================================================================
Tenant ID                     The Microsoft Azure tenant, in GUID format.
Client ID                     The client ID (sometimes called 'Application ID'), in GUID format
Secret                        A secret configured for the above client ID
============================  =======================================================================================

The Azure application needs the following permissions:

============================  =============  ========================================================================
Permission                    Type           Description
============================  =============  ========================================================================
Files.ReadWrite.All           Application    Read and write files in all site collections
============================  =============  ========================================================================

Configuration
=============

1. Obtain the parameters from the Azure application.
2. In Open Forms, navigate to: **Configuration** > **Overview**. In the **Registration plugin** group, click on **Configuration** for the **Microsoft Graph (OneDrive/SharePoint)** line.

   a. Click **Microsoft Graph Service toevoegen**.
   b. Fill out the form with the requested parameters; note the *Label* field is for internal use.
   c. Click **Opslaan**

3. Navigate to: **Configuration** > **Microsoft Graph registration**

   a. Select the *Microsoft Graph Service* we created above.
   b. Click **Opslaan**

The Microsoft Graph configuration is now completed and can be selected as registration backend in the form builder.


Technical
=========

================  ===================
Service           Supported versions
================  ===================
Microsoft Graph   1.0
================  ===================
