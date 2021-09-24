.. _configuration_prefill_kvk:

==========
KvK Zoeken
==========

**Supported versions**: 1.0

The `KvK`_ (Kamer van Koophandel) is a government organisation that contains 
information about businesses operating in the Netherlands. The KvK provides an 
API to retrieve information about businesses. Open Forms can be configured to 
access this API in order to prefill business information within a form.

.. note::

   You can access a test environment for this API that contains a very limited
   set of KvK numbers and test data.

.. warning::

   The KvK has a deprecated "Search API" which is different from their 
   "Zoeken API". Open Forms supports the "Zoeken API".


1. Obtain a `Kvk API Key`_ from the KvK.
2. In Open Forms, navigate to: **Configuration** > **Services**
3. Click **Add service** and fill in the following details:

   * **Label**: *Fill in a human readable label*, for example: ``My KvK Zoeken API``
   * **Type**: ORC (Overige)
   * **API root URL**: *The API URL provided by KvK*
   * **Authorization type**: API key
   * **Header key**: X-Api-Key
   * **Header value**: *The KvK API key obtained in step 1*
   * **OAS**: *URL to the Open API-specification provided by KvK (typically, they show the link to the API specification below their API title as CMS uploaded file)*

4. Click **Save**
5. Navigate to **Configuration** > **KvK configuration**
6. Select for the **Haal Centraal API**, the **[ORC (Overige)] My KvK Zoeken API**
   option, that we just created in step 3.
7. Click **Save**

The KvK configuration is now completed.


.. _`KvK`: https://www.kvk.nl/
.. _`KvK API key`: https://developers.kvk.nl/
