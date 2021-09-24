.. _configuration_prefill_haal_centraal:

==========================
Haal Centraal BRP bevragen
==========================

`Haal Centraal`_ is an initiative to transform the currently used SOAP-services
to consult the base registration, to modern RESTful API's.

The `Haal Centraal BRP bevragen API`_ allows you to retrieve personal 
information about the person filling out the form, based on the BSN.

.. note::

   This service contains sensitive data and requires a connection to a specific
   client system. Currently however, there are very few suppliers who offer 
   this service.

   On the `Haal Centraal BRP bevragen API`_ Github, you can request credentials 
   for a test environment that uses an API key.

1. Obtain credentials to access the Haal Centraal BRP bevragen API
2. In Open Forms, navigate to: **Configuration** > **Services**
3. Click **Add service** and fill in the following details:

   * **Label**: *Fill in a human readable label*, for example: ``My BRP API``
   * **Type**: ORC (Overige)
   * **Api root url**: *URL provided by supplier*
   * **Authorization type**: API key *(but can differ per supplier)*
   * **Header key**: Authorization
   * **Header value**: *The API key from step 1*
   * **OAS**: *URL to the Open API-specification provided by supplier or use the Github raw URL*

4. Click **Save**
5. Navigate to **Configuration** > **Haal Centraal configuration**
6. Select for the **Haal Centraal API**, the **[ORC (Overige)] My BRP API**
   option, that we just created in step 3.
7. Click **Save**

The Haal Centraal configuration is now completed.

.. _`Haal Centraal BRP bevragen API`: https://github.com/VNG-Realisatie/Haal-Centraal-BRP-bevragen
.. _`Haal Centraal`: https://vng-realisatie.github.io/Haal-Centraal/
