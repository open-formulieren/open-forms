.. _examples_objects_prefill:

===========================================================
Formulier met (product)gegevens voorinvullen (Objecten API)
===========================================================

In dit voorbeeld maken we een formulier bestaande uit één stap om een fictieve
vergunning aan te vragen. Er zijn gegevens van een eerdere aanvraag beschikbaar.

In dit voorbeeld gaan we er van uit dat u een
:ref:`eenvoudig formulier <example_simple_form>` kan maken.

.. seealso:: De :ref:`technische configuratie <configuration_prefill_objects_api>` moet
   gedaan zijn om dit na te kunnen bouwen.

Objecttype inrichten
====================

**Objecttypen API**

:external+objecttypes:ref:`Maak een objecttype <admin_objecttype>` aan met het volgende
JSON Schema:

.. code-block:: json

    {
      "type": "object",
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "required": [
        "bsn",
        "identifier",
        "startDate",
        "endDate"
      ],
      "properties": {
        "bsn": {
          "type": "string",
          "pattern": "^[0-9]{9}$",
          "description": "A valid Dutch BSN (Burger Service Number) must be exactly 9 digits."
        },
        "endDate": {
          "type": "string",
          "format": "date",
          "description": "The end date in YYYY-MM-DD format."
        },
        "remarks": {
          "type": "string",
          "description": "Optional remarks or notes for additional information."
        },
        "startDate": {
          "type": "string",
          "format": "date",
          "description": "The start date in YYYY-MM-DD format."
        },
        "identifier": {
          "type": "string",
          "pattern": "^[A-Z0-9-]+$",
          "description": "Unique identifier, typically composed of alphanumeric characters and dashes."
        }
      },
      "additionalProperties": false
    }

**Objecten API**

Zorg dat het bovenstaande objecttype geregistreerd is, en maak dan in de Objecten API
een record aan met de volgende gegevens:

.. code-block:: json

    {
      "bsn": "123456782",
      "endDate": "2024-12-31",
      "remarks": "Test initieel object aanmaken.",
      "startDate": "2024-12-13",
      "identifier": "VOORBEELD-123"
    }

In de Objecten API zie je in de beheeromgeving van elke record het UUID, bijvoorbeeld
``05a0972b-c604-4b58-bd7d-6d456fb2987b``.

.. tip:: Schrijf ergens het UUID van het object op - deze hebben we straks nodig.

Formulier aanmaken
==================

#. Maak een formulier aan met de volgende componenten in een formulierstap:

   * Tekstveld met label **Referentienummer**, niet verplicht.
   * Datumveld met label **Van**, verplicht.
   * Datumveld met label **Tot**, verplicht.
   * Tekstvlak met label **Opmerkingen / extra informatie**

#. Vink "Vereist authenticatie" aan op de formulierstap.
#. Selecteer één van de (demo) DigiD inlogopties bij de formulierauthenticatiemethoden.
#. Maak een gebruikersvariabele aan met de naam **Aanvraaggegevens** en datatype
   ``object``.
#. Klik het potlood-icoontje aan in de kolom "Prefill" van de gebruikersvariabele. Je
   kan nu de opties instellen.

    * Bij **Plugin** selecteer je "Objecten API". Er komen nu extra opties in beeld.
    * Voor **API-groep** selecteer je de groep die aangemaakt is door een beheerder.
    * Selecteer bij **Objecttype** het vergunning-objecttype wat eerder aangemaakt is.
    * Selecteer bij **Versie** de meest recente versie.
    * Bij **Path to auth attribute** kies je voor ``bsn``. De opties in deze lijst komen
      uit het geselecteerde objecttype.

    De instellingen moeten op de onderstaande screenshot lijken:

    .. image:: _assets/product_prefill_options_1.png
       :alt: Screenshot van de geselecteerde opties in de dropdowns.

    Vervolgens stellen we in waar de individuele attributen toegekend worden.

    * Scroll omlaag bij de instellingen totdat de "Variabelekoppleingen" in beeld staan.
    * Klik op **Variabele toevoegen**, en kies voor de formuliervariabele
      "Referentienummer", met brondpad ``identifier`` uit het objecttype.
    * Klik op **Variabele toevoegen**, en kies voor de formuliervariabele
      "Van", met brondpad ``startDate`` uit het objecttype.
    * Klik op **Variabele toevoegen**, en kies voor de formuliervariabele
      "Tot", met brondpad ``endDate`` uit het objecttype.
    * Klik op **Variabele toevoegen**, en kies voor de formuliervariabele
      "Opmerkingen / extra informatie", met brondpad ``remarks`` uit het objecttype.

    .. image:: _assets/product_prefill_options_2.png
       :alt: Screenshot met de variabelekoppelingen in een tabel.

    * Klik op "Opslaan" om de instellingen te bewaren.

#. Sla het formulier op.

Formulier invullen
==================

Om de vooringevulde gegevens te zien moet je de gegevensreferentie meegeven in de
formulierlink. Stel dat het formulier normaal beschikbaar is op
``https://forms.example.com/voorbeeld/``, dan wordt de nieuwe URL met
voorinvullen:

.. code-block:: none

    https://forms.example.com/voorbeeld/?initial_data_reference=05a0972b-c604-4b58-bd7d-6d456fb2987b

Hier gebruik je het UUID van het Object dat de brongegevens bevat.

Bonus: registreren in de Objecten API
=====================================

Je kan dit formulier ook weer registreren in de Objecten API. Belangrijk hierbij is dat
je dan:

* Bij de variabelen de ``auth_bsn`` statische variabele aan het ``bsn``-attribuut in het
  objecttype koppelt.
* Bij de variabelen de registratievariabele ``public_reference`` aan het
  ``identifier``-attribuut in het objecttype koppelt.

Nu kan je objecten aanmaken, en deze gelijk weer gebruiken als bron voor
prefill-gegevens.

.. tip:: Je kan ook het oorspronkelijke object wat voor prefill gebruikt is weer
   bijwerken tijdens de registratie! Open hiervoor de registratie-opties voor de
   Objecten API plugin en scroll naar "Update existing objects". Vink
   **Bestaand object bijwerken** aan, en selecteer bij **Path to auth attribute** weer
   het ``bsn``-attribuut.

   .. image:: _assets/product_prefill_options_3.png
       :alt: Screenshot van registratieopties die "bijwerken" in ingeschakelde stand toont.
