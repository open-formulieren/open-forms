=======
Prefill
=======

In dit voorbeeld tonen we hoe u een prefill kunnen gebruiken.  Prefill is een optie zodat
een formulier prefilled met informatie is.  Met dit voorbeeld tonen we hoe u de
:ref:`KvK <configuration_prefill_kvk>` prefill kan gebruiken maar we hebben op dit moment ook
:ref:`StUF-BG <configuration_prefill_stuf_bg>` prefill en
:ref:`Haal Centraal Bevragen personen <configuration_prefill_haal_centraal>` prefill dat u kan gebruiken.


Configuratie
============

Voor dit formulier is bepaalde configuratie nodig. Hieronder staan de onderdelen
die geconfigureerd moeten zijn:

* :ref:`KvK configuratie <configuration_prefill_kvk>`


Formulier maken
===============

1. Maak een formulier aan met de volgende gegevens:

   * **Naam**: KvK demo

2. Klik op het tabblad **Stappen en velden**.
3. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe formulierdefinitie**.
4. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

    * **Naam**: KvK Gegevens

5. Scroll naar de sectie **Velden**.
6. Sleep een **Text Field** component op het witte vlak.
7. Vul de volgende gegevens in en druk daarna op **Save**:

   * **Label**: Handelsnaam

8. Onder de **Pre-fill** tab:

    * **Plugin**: ``KvK Bedrijf via KvK-nummer``
    * **Plugin attribute**: ``handelsnaam``

9. (Optioneel) Herhalen stappen 6 naar 8 met andere **Plugin attribute**
10. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken.
