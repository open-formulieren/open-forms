===================================
Velden afhankelijk van inlogmethode
===================================

Er kunnen per formulier meerdere inlogmethoden worden geselecteerd. Afhankelijk
van de inlogmethode kunnen andere velden worden getoond. Dit kan handig zijn
voor formulieren die geschikt zijn voor bedrijven en voor particulieren.

.. note::
    
    Open Formulieren ondersteunt niet direct de logica om op basis van 
    inlogmethode bepaalde velden wel of niet te tonen. We beschrijven hier een
    methode om het toch voor elkaar te krijgen. Dit vereist wel dat er een 
    koppeling met de :ref:`KvK <configuration_prefill_kvk>` en met 
    :ref:`StUF-BG <configuration_prefill_stuf_bg>` of 
    :ref:`Haal Centraal Bevragen personen <configuration_prefill_haal_centraal>`
    is ingesteld.

In dit voorbeeld gaan we er van uit dat u een
:ref:`eenvoudig formulier <example_simple_form>` heeft en combineren we de kennis van
:ref:`voorinvullen <example_prefill>` met :ref:`logica <example_logic_rules>`.


.. note::

    U kunt dit voorbeeld downloaden en :ref:`importeren <manual_export_import>`
    in Open Formulieren.

    Download: :download:`fields_for_logintype.zip <_assets/fields_for_logintype.zip>`


Configuratie
============

Voor dit formulier is bepaalde configuratie nodig. Hieronder staan de onderdelen
die geconfigureerd moeten zijn:

* :ref:`KvK configuratie <configuration_prefill_kvk>`
* :ref:`StUF-BG <configuration_prefill_stuf_bg>` of 
  :ref:`Haal Centraal Bevragen personen <configuration_prefill_haal_centraal>`


Formulier maken
===============

1. Maak een formulier aan met de volgende gegevens:

   * **Naam**: Velden op basis van inlogmethode

2. Klik op het tabblad **Stappen en velden**.
3. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe formulierdefinitie**.
4. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

    * **Naam**: Uw gegevens

5. Scroll naar de sectie **Velden**.
6. Sleep een **Tekst** component op het witte vlak.
7. Vul de volgende gegevens in en druk daarna op **Opslaan**:

   * **Label**: Handelsnaam

8. Onder de **Pre-fill** tab:

    * **Plugin**: ``KvK Bedrijf via KvK-nummer``
    * **Plugin attribute**: ``handelsnaam``

9. Sleep een **Tekst** component op het witte vlak.
10. Vul de volgende gegevens in en druk daarna op **Opslaan**:

   * **Label**: Achternaam

11. Onder de **Pre-fill** tab:

    * **Plugin**: ``Haal Centraal``
    * **Plugin attribute**: ``Naam > Geslachtsnaam``

12. Klik op het tabblad **Logica**.
13. Voeg de volgende regel toe:

    * Als *Handelsnaam* - *is niet gelijk aan* - *de waarde* - (laat leeg)

        * Dan *wijzig een attribuut van een veld/component* - *Handelsnaam* - *verborgen* - *Nee*

        * en *wijzig een attribuut van een veld/component* - *Achternaam* - *verborgen* - *Ja*

14. Voeg nog een regel toe:

    * Als *Achternaam* - *is niet gelijk aan* - *de waarde* - (laat leeg)

        * Dan *wijzig een attribuut van een veld/component* - *Achternaam* - *verborgen* - *Nee*

        * en *wijzig een attribuut van een veld/component* - *Handelsnaam* - *verborgen* - *Ja*

15. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken.
