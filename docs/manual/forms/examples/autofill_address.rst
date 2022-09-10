===========================
Adres automatisch aanvullen
===========================

In dit voorbeeld maken we een deel-formulier bestaande uit 1 stap, waarbij de
straatnaam en stad automatisch worden ingevuld zodra de postcode en huisnummer
zijn ingevuld.

In dit voorbeeld gaan we er van uit dat u een
:ref:`eenvoudig formulier <example_simple_form>` kan maken.

.. note::

    U kunt dit voorbeeld downloaden en :ref:`importeren <manual_export_import>`
    in Open Formulieren.

    Download: :download:`autofill_address.zip <_assets/autofill_address.zip>`


Configuratie
============

Voor dit formulier is bepaalde configuratie nodig. Hieronder staan de onderdelen
die geconfigureerd moeten zijn:

* :ref:`BAG configuratie <configuration_prefill_bag>`: Voor het opzoeken van adressen.


Formulier maken
===============

1. Maak een formulier aan met de volgende gegevens:

   * **Naam**: Adres demo

2. Klik op het tabblad **Stappen en velden**.
3. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe
   formulierdefinitie**.
4. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

    * **Naam**: Adresgegevens

5. Scroll naar de sectie **Velden**.
6. Sleep een **Postcode Field** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Postcode

7. Sleep een **Tekstveld** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Huisnummer

8. Sleep een **Tekstveld** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Straat

   Onder de **Location** tab:

     * **Straatnaam afleiden**: *Aangevinkt*
     * **Postcodecomponent**: ``Postcode (postcode)``
     * **Huisnummercomponent**: ``Huisnummer (huisnummer)``

9. Sleep een **Tekstveld** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Stad

   Onder de **Location** tab:

   * **Stad afleiden**: *Aangevinkt*
   * **Postcodecomponent**: ``Postcode (postcode)``
   * **Huisnummercomponent**: ``Huisnummer (huisnummer)``

10. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken.
