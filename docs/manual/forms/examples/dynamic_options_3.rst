.. _example_logic_dynamic_options_3:

==========================================================================
Formulier met (extra) opties in selectievakjes, keuzelijst en radio-velden
==========================================================================

In dit voorbeeld maken we een deel-formulier waarbij een vaste groep keuzeopties
dynamisch uitgebreid wordt op basis van logica-regels.

Deze functionaliteit kan op eenzelfde manier worden gebruikt voor de "radio"-,
"keuzelijst"- en de "selectievakjes"-componenten.

.. note::

    U kunt dit voorbeeld downloaden en :ref:`importeren <manual_export_import>`
    in Open Formulieren.

    Download: :download:`dynamische-keuzelijsten.zip <_assets/dynamische-keuzelijsten.zip>`

Formulier maken
===============

#. Maak een formulier aan met de volgende gegevens:

    * **Naam**: Dynamische keuzelijsten

#. Klik op het tabblad **Variabelen**. Klik hierbinnen op het tabblad
   **Gebruikersvariabelen**.

#. Voeg een variabele toe door op **Variabele toevoegen** link te klikken, en voer in:

    * **Naam**: Checkbox options
    * **Datatype**: Lijst (array)
    * **Beginwaarde**: vink *"Gebruik ruwe JSON-invoer"* aan en voer de JSON-array in:

      .. code-block:: json

          [
            [
              "option1",
              "Option 1"
            ],
            [
              "option2",
              "Option 2"
            ]
          ]

#. Klik op het tabblad **Stappen en velden**.

#. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe
   formulierdefinitie**.

#. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

    * **Naam**: Variabele selectievakjesopties

#. Scroll naar de sectie **Velden**.

#. Sleep een **Selectievakje** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

    * **Label**: Toon optie 3

#. Sleep een **Selectievakjes** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

    * **Label**: Variabele opties selectievakjes
    * **Beschrijving**: De beschikbare opties zijn afhankelijk van eerdere antwoorden.

    * **Keuzeopties**: *Variabele*
    * **Opties-expressie**:

      .. code-block:: json

       {
         "var": "checkboxOptions"
       }

    Deze referentie komt overeen met de sleutel van de eerder toegevoegde
    gebruikersvariabele.

#. Klik op het tabblad **Logica** en voeg een eenvoudige regel toe.

#. Kies als triggervoorwaarde:

    * Als "Variabele selectievakjesoptie: Toon optie 3 (toonOptie3)"
    * "is gelijk aan"
    * "de waarde"
    * "Ja"

#. Voeg een actie toe:

    * dan "zet de waarde van een variabele/component"
    * "Checkbox options (checkboxOptions)"
    * voer de volgende JsonLogic in:

      .. code-block:: json

         {
           "merge": [
             {
               "var": "checkboxOptions"
             },
             [
               [
                 "option3",
                 "Option 3"
               ]
             ]
           ]
         }

#. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken.

.. note::

    Deze expressie gebruik de JsonLogic `merge`_ operatie om de bestaande
    gebruikersvariabele uit te breiden met extra keuzeopties. U kunt vrij
    gebruikersvariabelen combineren zolang de variabele voor de selectievakjes component
    een lijst van opties (waarde en label) bevat.

.. _merge: https://jsonlogic.com/operations.html#merge
