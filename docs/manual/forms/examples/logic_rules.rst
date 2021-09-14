===========================
Formulier met logica regels
===========================

In dit voorbeeld maken we een deel-formulier bestaande uit 1 stap, waarbij
de geboorte datum ingevuld door de gebruiker beïnvloedt of het formulier kan worden
ingediend.

In dit voorbeeld gaan we er van uit dat u een
:ref:`eenvoudig formulier <example_simple_form>` kan maken.

Formulier maken
===============

1. Maak een formulier aan met de volgende gegevens:

    * **Naam** Rijbewijs aanvraag demo

2. Klik op het tabblad **Stappen en velden**.
3. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe
   formulierdefinitie**.
4. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

    * **Naam**: Persoonlijke gegevens

5. Scroll naar de sectie **Velden**.
6. Sleep een **Text Field** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Save**:

    * **Label**: Naam

7. Herhaal stap 6. maar met:

    * **Label**: Achternaam

8. Sleep een **Date Field** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Save**:

    * **Label**: Geboorte datum
    * Klik op het tabblad **Validation** en selecteer **Required**.

9. Onder de formulier velden, klik op **Opmaak**. Sleep een **Content** component op het
   witte vlak. Vul de volgende gegevens in en druk daarna op **Save**:

    * Onder **Content component**: Om een rijbewijs te kunnen aanvragen moet u ouder dan 18 jaar zijn.
    * **Label**: Warning.
    * Selecteer **Hidden**.

10. Klik op het tabblad **Logica**.
11. Klik op **Regel toevoegen**.
12. Selecteer de **Geboorte datum** component van de drop down. Er verschijnt dan een nieuwe drop down.
13. Selecteer **is groter dan**. Er verschijnt dan nog een drop down.
14. Selecteer **today**. Er verschijnen dan een nieuwe drop down en drie nummer velden voor jaren, manden en dagen.
15. Selecteer **minus** en vult **18** in het jaren veld.

.. note::

    Deze regel betekent: 'Als de geboorte datum van de gebruiker later
    is dan vandaag 18 jaar geleden'. Het is dus een check dat
    de gebruiker 18 jaar of ouder is op het moment dat hij/zij het formulier invult.

16. Klik op **Voeg actie toe**.
17. Selecteer **blokkeer doorgaan naar de volgende stap**.
18. Klik opnieuw op **Voeg actie toe**.
19. Selecteer **wijzig een attribuut van een veld/component.**. Er verschijnen dan nieuwe drop-downs.
20. Selecteer de component **Warning** in de eerst drop down, dan **verborgen** en **Nee** in de laatste drop-down.

.. note::

    Deze twee acties betekenen: als de gebruiker jonger dan 18 is, dan blokkeer
    doorgaan naar de volgende formulier stap en maak de 'Warning component' zichtbaar.

.. image:: _assets/rijbewijs_logica.png
    :width: 100%

21. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken.
