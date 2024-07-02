.. _examples_auth_static_variables:

===========================
Formulier met authenticatie
===========================

In dit voorbeeld maken we een fictief formulier bestaande uit 1 stap, waarbij
logica en :ref:`vaste variabelen <manual_forms_variables>` worden
gebruikt om te zien of de gebruiker als persoon of als bedrijf ingelogd is.

In dit voorbeeld gaan we er van uit dat u een
:ref:`formulier met eenvoudige logica <example_logic_rules>` kan maken en dat
u op de hoogte bent van hoe :ref:`logica <manual_logic>` werkt.


Formulier maken
===============

#. Maak een formulier aan met de volgende gegevens:

   * **Naam**: Authenticatie en variabelen demo
   * **Inlogopties** > **DigiD simulatie**: *Aangevinkt*
   * **Inlogopties** > **Demo KvK-Nummer**: *Aangevinkt*

#. Klik op het tabblad **Stappen en velden**.
#. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe
   formulierdefinitie**.
#. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

   * **Naam**: Eerste stap

#. Scroll naar de sectie **Velden**.
#. Sleep een **Vrije tekst** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Content BSN
   * Onder **Content component**: "U bent ingelogd als persoon."
   * **Verborgen**: *Aangevinkt*

#. Sleep een **Vrije tekst** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Content KvK
   * Onder **Content component**: "U bent ingelogd als bedrijf."
   * **Verborgen**: *Aangevinkt*

#. Sleep een **Vrije tekst** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Content Anoniem
   * Onder **Content component**: "U bent niet ingelogd."

#. Druk daarna op **Opslaan en opnieuw bewerken**.
#. Klik op het tabblad **Logica** en voeg twee eenvoudige regels toe:

   * | De eerste met de trigger:
     | Als **Authentication BSN (auth_bsn)** > **is niet gelijk aan** > **de waarde** > (*leeg*)
     | en acties:
     | dan **Wijzig een attribuut van een veld/component** > **Content BSN** > **verborgen** > **Nee**
     | dan **Wijzig een attribuut van een veld/component** > **Content Anoniem** > **verborgen** > **Ja**

   * | De tweede met de trigger:
     | Als **Authentication KvK (auth_kvk)** > **is niet gelijk aan** > **de waarde** > (*leeg*)
     | en acties:
     | dan **Wijzig een attribuut van een veld/component** > **Content KvK** > **verborgen** > **Nee**
     | dan **Wijzig een attribuut van een veld/component** > **Content Anoniem** > **verborgen** > **Ja**

#. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken. Als u de met de demo KvK-Nummer / DigiD simulatie plugin inlogt, dan verschijnt in het
formulier de "vrije tekst"-component "Content KvK" / "Content BSN". Als u het formulier start zonder in te loggen, dan
zal alleen de "vrije tekst"-component "Content Anoniem" zichtbaar zijn.
