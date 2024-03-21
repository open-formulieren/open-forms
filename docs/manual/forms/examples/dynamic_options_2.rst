.. _example_logic_dynamic_options_2:

=============================================================
Formulier met dynamische opties op basis van het huidige jaar
=============================================================

In dit voorbeeld maken we een deel-formulier bestaande uit 1 stap, waarbij de
opties van een "keuzelijst" component dynamisch worden aangepast aan de hand
de waarde van een variabele. In dit voorbeeld `current_year`.

Deze functionaliteit kan op eenzelfde manier worden gebruikt voor de "radio"
component en de "selectievakjes" component.


Formulier maken
===============

#. Maak een formulier aan met de volgende gegevens:

    * **Naam**: Keuzelijst jaar demo

#. Klik op het tabblad **Stappen en velden**.
#. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe
   formulierdefinitie**.
#. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

    * **Naam**: Aanvraag gegevens

#. Scroll naar de sectie **Velden**.
#. Sleep een **Keuzelijst** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Jaar aanvraag
   * **Beschrijving**: Voor welk jaar vraagt u de subsidie aan?

   * **Keuzeopties**: *Variabele*
   * **Opties-expressie**:

   .. code-block:: json

    {
      "merge": [
        { "-": [{ "var": "current_year" }, 3] },
        { "-": [{ "var": "current_year" }, 2] },
        { "-": [{ "var": "current_year" }, 1] },
        { "var": "current_year" },
        { "+": [{ "var": "current_year" }, 1] }
      ]
    }

#. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken.

.. note::

    Deze expressie gebruik de JsonLogic `merge`_ operatie om een lijst te
    maken van 5 getallen. De `var`_ operatie wordt gebruikt om de waarde van de
    door open formulieren voorgedefinieerde, vaste variabele `current_year` op te vragen
    en die vervolgens te bewerken met `+` en `-`.

    Stel we leven in het jaar 2023, dan zal het resultaat de lijst
    `[2020, 2021, 2022, 2023, 2024]` zijn. Deze getallen zullen dan zowel voor
    de waarden als de labels gebruikt worden.

.. note::

    De waarde van `current_year` is een int (geheel getal). In
    :ref:`manual_templates` worden getallen standaard met een `.`
    scheidingsteken na de duizendtallen getoond. Wat voor een jaartal natuurlijk
    niet wenselijk is. Door gebruik te maken van de `stringformat`_
    sjabloonfilter kunt u dit voorkomen: `{{ current_year | stringformat:"d" }}`


.. _merge: https://jsonlogic.com/operations.html#merge
.. _var: https://jsonlogic.com/operations.html#var
.. _stringformat: https://docs.djangoproject.com/en/4.2/ref/templates/builtins/#stringformat
