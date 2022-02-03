.. _configuration_prefill_kvk:

================
KvK Basisprofiel
================

The `KvK`_ (Kamer van Koophandel) is a government organisation that contains
information about businesses operating in the Netherlands. The KvK provides an
API to retrieve information about businesses. Open Forms can be configured to
access this API in order to prefill business information within a form.

.. note::

   You can access a test environment for this API that contains a very limited
   set of KvK numbers and test data.

.. warning::

   The KvK has a deprecated "Search API" which is different from their
   "Zoeken API". Open Forms supports the "Zoeken API" and the 
   "Basisprofiel API".

.. _`KvK`: https://www.kvk.nl/


Configuration
=============

1. Obtain a `Kvk API Key`_ from the KvK.
2. In Open Forms, navigate to: **Miscellaneous** > **KvK configuration**
3. For **KvK API Basisprofiel** select the appropriate service, or create it. If the 
   appropriate service already exists, select it and go to step 10.
4. Click **Add** next to the **KvK API Basisprofiel** field and fill in the following
   details:

   * **Label**: *Fill in a human readable label*, for example: ``My KvK Basisprofiel API``
   * **Type**: ORC (Overige)
   * **API root URL**: *The API URL provided by KvK but typically:* ``https://api.kvk.nl/api/v1/basisprofielen/``
   * **Authorization type**: API key
   * **Header key**: ``apikey``
   * **Header value**: *The KvK API key obtained in step 1*
   * **OAS file**: *Upload the KvK Basisprofiel API OAS (typically, they show the link to the API specification below their API title as CMS uploaded file)*

5. Click **Save** in the popup to save and close it.
6. Technically you are done. Prefilling uses the KvK Basisprofiel API. However,
   to validate KvK-numbers, you also need to configure the KvK Zoeken API. If 
   this is not used, you can go to step 10.
7. For **KvK API Zoeken** select the appropriate service, or create it. If the 
   appropriate service already exists, select it and go to step 10.
8. Click **Add** next to the **KvK API Zoeken** field and fill in the following
   details:

   * **Label**: *Fill in a human readable label*, for example: ``My KvK Zoeken API``
   * **Type**: ORC (Overige)
   * **API root URL**: *The API URL provided by KvK but typically:* ``https://api.kvk.nl/api/v1/zoeken/``
   * **Authorization type**: API key
   * **Header key**: ``apikey``
   * **Header value**: *The KvK API key obtained in step 1 (same as for KvK API Basisprofiel)*
   * **OAS file**: *Upload the KvK Zoeken API OAS (typically, they show the link to the API specification below their API title as CMS uploaded file)*

9. Click **Save** in the popup to save and close it.
10. Click **Save** to save the KvK configuration.

The KvK configuration is now completed.

.. _`KvK API key`: https://developers.kvk.nl/


Technical
=========

================  ===================
API               Supported versions
================  ===================
Basisprofiel API  1.3
Zoeken API        1.3
================  ===================
