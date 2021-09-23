.. _configuration_prefill_kvk:

===
KvK
===

The `KvK`_ (Kamer van Koophandel) is a government organisation that contains information about
businesses operating in the Netherlands.  The KvK provides an API to retrieve information
about businesses.  Open Forms can be configured to access this API in order to prefill
business information within a form.

1. Obtain a `Kvk API Key`_ from KvK.
2. In Open Forms, navigate to: **Configuration** > **KvK configuration**
3. Click the **green plus button** and fill in the following details:

   * **Label**: KvK API
   * **Type**: ORC (Overige)
   * **API root URL**: *The API URL provided by KvK*
   * **Authorization type**: API key
   * **Header key**: X-Api-Key
   * **Header value**: *The KvK API key obtained in step 1*
   * **OAS**: *URL to the Open API-specification provided by KvK*

4. Click **Save**

The KvK configuration is now completed.


.. _`KvK`: https://www.kvk.nl/
.. _`KvK API key`: https://developers.kvk.nl/
