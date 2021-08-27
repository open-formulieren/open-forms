.. _configuration_bag:

=================
BAG configuration
=================

The BAG (Basisregistratie Adressen en Gebouwen) is a database from the 
`Kadaster`_ that can be accessed via the `BAG API`_. Open Forms can be 
configured to access this API to autocomplete addresses.

1. Obtain a `BAG API key`_ from Kadaster.
2. In Open Forms, navigate to: **Configuration** > **Services**
3. Click **Add service** and fill in the following details:

   * **Label**: BAG (Kadaster)
   * **Type**: ORC (Overige)
   * **API root URL**: https://api.bag.kadaster.nl/lvbag/individuelebevragingen/v2/
   * **Authorization type**: API key
   * **Header key**: X-Api-Key
   * **Header value**: *The BAG API key obtained in step 1*
   * **OAS**: `https://raw.githubusercontent.com/lvbag/BAG-API/master/Technische%20specificatie/Yaml's/BAG%20API%20Individuele%20Bevragingen/resolved/individuelebevragingen/v2/adressen.yaml`

4. Click **Save**
5. Navigate to **Configuration** > **BAG configuration**
6. Select for the **BAG service**, the **[ORC (Overige)] BAG (Kadaster)** 
   option.
7. Click **Save**

The BAG configuration is now completed.


.. _`Kadaster`: https://www.kadaster.nl/
.. _`BAG API`: https://bag.basisregistraties.overheid.nl/
.. _`BAG API key`: https://www.kadaster.nl/zakelijk/producten/adressen-en-gebouwen/bag-api-individuele-bevragingen