.. _example_form_with_geometry:

================================================
Kaartmateriaal en registratie in de Objecten API
================================================

In dit formulier maken we gebruik van de "Kaart"-component om coördinaten van een
locatie uit te vragen en te registreren. Het formulier wordt gekoppeld met de
`Objecten API`_ voor het registreren van de inzendingsgegevens.

We gaan er van uit dat de koppeling met de Objecten API
:ref:`geconfigureerd <configuration_registration_objects>` is, en gebruiken als
objecttype-URL ``https://objecttype-example.nl/api/v2/objecttype/123``.

Formulier maken
===============

We bouwen een formulier met twee kaarten - één kaart wordt gebruikt voor "dé" geometrie
van het hele Object in de Objecten API en de andere kaart wordt als extra/vrije-vorm
attribuut meegestuurd.

#. Maak een formulier aan met de volgende gegevens:

   * **Naam**: Kaartgegevens registreren in de Objecten API

#. Klik op het tabblad **Stappen en velden**.
#. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe
   formulierdefinitie**.
#. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

   * **Naam**: Kaarten

#. Scrol naar beneden en klik de sectie **Speciale velden** aan.
#. Sleep een **Kaart** component op het witte vlak en vul de volgende
   gegevens in:

   * **Label**: Hoofdgeometrie

#. Klik vervolgens de **Registratie** tab aan en vul de volgende gegevens in:

   * **Registratie-attribuut**: Locatie > Coördinaten

#. Druk daarna op **Opslaan**.

#. Sleep een tweede **Kaart** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Extra geometrie

#. Klik op het tabblad **Registratie**.
#. Klik op **Registratiepluginoptie toevoegen** en vul de volgende gegevens in:

    * **Naam**: Objecten API
    * **Registratiemethode**: Objecten API registratie
    * **Objecttype**: ``https://objecttype-example.nl/api/v2/objecttype/123``
    * **JSON-inhoud sjabloon**:

      .. code-block:: django

          {
              "extraGeometrie": {% as_geo_json variables.extraGeometrie %}
          }

#. Druk daarna op **Opslaan en opnieuw bewerken**. Het formulier kan nu ingevuld en
   ingestuurd worden.


.. note:: Het inrichten van het Objecttype en de Objecten API is geen onderdeel van
   dit voorbeeld, maar wel essentieel om zonder fouten formulierinzendingen te kunnen
   verwerken.


Toelichting
===========

De eerste kaart is ingesteld via de "Registratie" tab op het component. Dit zorgt ervoor
dat de Objecten API-registratieplugin dit veld gebruikt voor "de" geometrie van het object
in de Objecten API. Deze kent hiervoor namelijk één vast attribuut.

Echter, we kunnen extra geometrieën alsnog meesturen (als het objecttype dit modelleert),
dit doen we door het als ``GeoJSON`` te formatteren met de ``{% as_geo_json ... %}``
sjablooncode.

.. note:: Het is niet de bedoeling dat meerdere kaarten via de "Registratie" tab gekoppeld
   worden aan het Locatie-attribuut - als je dit wel doet, dan zal er slechts één component
   meegestuurd worden.

Het resulterende object wat naar de Objecten API gestuurd wordt ziet er uit als:

.. code-block:: json

    {
        "type": "https://objecttype-example.nl/api/v2/objecttype/123",
        "record": {
            "typeVersion": "1",
            "data": {
                "extraGeometrie": {
                    "type": "Point",
                    "coordinates": [52.37403, 4.88969]
                }
            },
            "startAt": "2023-01-01",
            "geometry": {
                "type": "Point",
                "coordinates": [51.9225, 4.47917]
            }
        }
    }

.. seealso::

    De :ref:`sjabloondocumentatie <manual_templates>` heeft een referentie van beschikbare
    template tags, met details voor de :ref:`objecten_api_registratie`.

.. _Objecten API: https://objects-and-objecttypes-api.readthedocs.io/
