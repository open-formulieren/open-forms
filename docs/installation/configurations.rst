.. _configurations:

=======================
Configurations
=======================

Various configurations can be configured within Open Forms to add data and validation to the forms.

BAG configuration
-----------------

The BAG configuration contains a single service to be configured.
To add a service you need to fill in the following information

* ``Label``: What you want to call the service.  Eg. ``Bag Service``

* ``Type``: The type of service this service is.  Currently it is limited to ``ORC (Overige)``

* ``Api root url``: The root of the url this service will communicate with. An example root url would be https://api.bag.kadaster.nl/lvbag/individuelebevragingen/v2/

* ``Authorization type``: The type of authorization the Api uses.  Will likely be ``API key``

* ``Header key``: The header key the Api will use to read the Api key.  Will likely be ``X-Api-Key``

* ``Header value``: The Api key.  An Api key can be requested from https://www.kadaster.nl/

* ``OAS``: A url where the OpenAPI 3 yaml file can be retrieved.  An example file would be https://raw.githubusercontent.com/lvbag/BAG-API/master/Technische%20specificatie/Yaml's/BAG%20API%20Individuele%20Bevragingen/resolved/individuelebevragingen/v2/adressen.yaml
