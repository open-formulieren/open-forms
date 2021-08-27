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

    Download: `autofill_address.zip`_


.. _`autofill_address.zip`: _assets/autofill_address.zip

Configuratie
============

Voor dit formulier is bepaalde configuratie nodig. Hieronder staan de onderdelen
die geconfigureerd moeten zijn:

* :ref:`BAG configuratie <configuration_bag>`: Voor het opzoeken van adressen.


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
   gegevens in en druk daarna op **Save**:

   * **Label**: Postcode

7. Sleep een **Text Field** component op het witte vlak, vul de volgende 
   gegevens in en druk daarna op **Save**:

   * **Label**: Huisnummer

8. Sleep een **Text Field** component op het witte vlak, vul de volgende 
   gegevens in en druk daarna op **Save**:

   * **Label**: Straat

   Onder de **Location** tab:
   
     * **Derive street name**: *Aangevinkt*
     * **Postcode component**: ``Postcode (postcode)``
     * **House number component**: ``Huisnummer (huisnummer)``

9. Sleep een **Text Field** component op het witte vlak, vul de volgende 
   gegevens in en druk daarna op **Save**:
  
   * **Label**: Stad
  
   Onder de **Location** tab:
    
   * **Derive city**: *Aangevinkt*
   * **Postcode component**: ``Postcode (postcode)``
   * **House number component**: ``Huisnummer (huisnummer)``

10. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken.
