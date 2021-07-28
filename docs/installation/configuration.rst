.. _installation_configurations:

==============
Configurations
==============

The various modules and plugins in Open Forms require some configuration before they can be used.

BAG configuration
=================

The BAG configuration contains a single service to be configured.
To add a service you need to fill in the following information

* ``Label``: What you want to call the service.  Eg. ``BAG (Kadaster)``

* ``Type``: The type of API.  Currently it is limited to ``ORC (Overige)``

* ``Api root url``: The root URL where the service can be consumed. For example: ``https://api.bag.kadaster.nl/lvbag/individuelebevragingen/v2/``

* ``Authorization type``: The type of authorization the Api uses.  Will likely be ``API key``

* ``Header key``: The HTTP header name to use for the API-key authorization. Will likely be ``X-Api-Key``.

* ``Header value``: The Api key.  An Api key can be requested from ``https://www.kadaster.nl/``

* ``OAS``: A url where the OpenAPI 3 yaml file can be retrieved.  An example file would be ``https://raw.githubusercontent.com/lvbag/BAG-API/afeb9eed4e615f7589328849308874cd3f139d13/Technische%20specificatie/Yaml's/BAG%20API%20Individuele%20Bevragingen/resolved/individuelebevragingen/v2/adressen.yaml``

