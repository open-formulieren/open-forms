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
2. In Open Forms, navigate to: **Configuration** > **Overview**.

   a. In the **Registration plugin** section, click on **Configuration** for 
      the **Microsoft Graph (OneDrive/SharePoint)** line.
   b. Click the **+**-sign (Add Microsoft Graph Service). A popup should show 
      up.
   c. Fill out the form with the requested parameters; note the **Label** field 
      is for internal use.
   d. Click **Save** to save this service configuration
   e. Click **Save** again to select the just added service configuration as 
      the default service.

3. Open any form, and open the **Registration** tab

   a. Select **Microsoft Graph (OneDrive/Sharepoint)** as registration backend.
   b. Optionally fill in the desired **Path** and **Drive ID**. The path value 
      supports the variables ``{{year}}``, ``{{month}}`` and ``{{day}}`` to 
      make dynamic paths.

Upon registration the submissions will be saved in the configured drive and path. Submissions for a particular form will
be in a folder named after the form slug, each in a subfolder with the submission reference name.
For example, if the configured path was ``/OpenForms/{{year}}``, and the form slug was ``drivers-licence-request``,
the data of a submission with reference ``OF-1234`` would be saved under the path 
``/OpenForms/2023/drivers-licence-request/OF-1234``.
In this folder, the submission PDF, attachments and JSON-data is stored.

.. note::

   It can be a little hard to find the Drive ID when using SharePoint which 
   typically works with "Sites". One trick is to head to the desired SharePoint 
   folder in the browser and modify the URL to retrieve the Drive ID.

   If the desired folder is shown in the browser, on a URL like this:

   ``https://example.sharepoint.com/sites/MY-SITE`` or ``https://example.sharepoint.com/sites/MY-SITE/Shared%20documents/MY-FOLDER/AllItems.aspx``

   The Drive ID can be found here by modifying the URL to:

   ``https://example.sharepoint.com/sites/MY-SITE/_api/v2.0/drives``

   Look for the ``id`` property which is the Drive ID.


Technical
=========

================  ===================
Service           Supported versions
================  ===================
Microsoft Graph   1.0
================  ===================
