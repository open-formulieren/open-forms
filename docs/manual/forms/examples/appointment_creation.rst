==============
Afspraak maken
==============

In dit voorbeeld tonen we u hoe u een formulier kan maken zodat de gebruikers een afspraak
kan maken met het formulier.

In dit voorbeeld gaan we er van uit dat u een
:ref:`eenvoudig formulier <example_simple_form>` kan maken.

Configuratie
============

* :ref:`Appointment configuratie <configuration_appointment>`

Formulier maken
===============

1. Maak een formulier aan met de volgende gegevens:

   * **Naam**: Afspraak demo

2. Klik op het tabblad **Stappen en velden**.
3. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe
   formulierdefinitie**.
4. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

    * **Naam**: Afspraakgegevens

5. Scroll naar de sectie **Velden**.
6. Sleep een **Select** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Save**:

   * **Label**: Producten

7. Sleep een **Select** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Save**:

   * **Label**: Locaties

8. Sleep een **Select** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Save**:

   * **Label**: Datums

9. Sleep een **Select** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Save**:

   * **Label**: Tijden

10. Sleep een **Text Field** component op het witte vlak, vul de volgende
    gegevens in en druk daarna op **Save**:

   * **Label**: Achternaam

11. Sleep een **Date Field** component op het witte vlak, vul de volgende
    gegevens in en druk daarna op **Save**:

   * **Label**: Geboortedatum

12. Klik op het tabblad **Afspraken**.
13. Kies de juiste componenten voor elke veld in deze tabblad.
14. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken.

.. note::

   De velden *Acternaam* en *Geboortedatum* mogen in een aparte formulierdefinitie (stap) aanwezig zijn maar
   de velden *Producten*, *Locaties*, *Datums*, en *Tijden* moeten in dezelfde formulierdefinitie (stap) aanwezig zijn.

