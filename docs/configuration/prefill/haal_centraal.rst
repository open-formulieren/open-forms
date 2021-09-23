.. _configuration_prefill_haal_centraal:

=============
Haal Centraal
=============

Haal Centraal is an API that allows you to retrieve personal information about the person
filling out the form.

1. Obtain a `Haal Centraal API key`_ from Kadaster.
2. In Open Forms, navigate to: **Configuration** > **Haal Centraal configuration**
3. Click the **Green Plus Button** and fill in the following details:

   * **Label**: Haal Centraal
   * **Type**: ORC (Overige)
   * **Api root url**:
   * **Authorization type**: API key
   * **Header key**: Authorization
   * **Header value**: Token *The api key from step 1*
   * **OAS**: *URL to the Open API-specification provided by Kadaster*

4. Click **Save**

.. _`Haal Centraal API key`: https://www.kadaster.nl/
