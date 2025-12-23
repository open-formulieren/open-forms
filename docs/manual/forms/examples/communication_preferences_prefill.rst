.. _examples_communication_preferences_prefill:

=========================================================
Formulier met vooringevulde voorkeurscommunicatieadressen
=========================================================

In dit voorbeeld maken we een formulier dat uit één stap bestaat, waarbij de
voorkeurscommunicatieadressen vooraf worden ingevuld.

In dit voorbeeld gaan we er van uit dat je een
:ref:`eenvoudig formulier <example_simple_form>` kan maken.

.. seealso:: De :ref:`technische configuratie <configuration_prefill_communication_preferences>`
   moet gedaan zijn om dit na te kunnen bouwen.

Formulier aanmaken
==================

Formulierstappen
----------------

#. Maak een nieuw formulier aan:

    * **Naam**: Communicatievoorkeur
    * Bij *Inloggen* > *Authenticatiemethode*: vink één van de inlogopties aan
      die ``biedt bsn aan`` of ``biedt kvk aan`` bevat.

#. Navigeer naar de tab *Stappen en velden* en voeg een nieuwe stap toe. Kies
   *Maak een nieuwe formulierdefinitie*:

    * **Naam**: E-mailadres en telefoonnummer
    * Vink **Vereist authenticatie** aan.

#. Klap vervolgens de "Speciale velden" open en voeg een Profiel-component toe:

    * **Label**: Voorkeursadressen

Pre-fill
--------

Nu stellen we het voorinvullen in, zodat de formulierstap wordt gevuld met de
voorkeurscommunicatieadresgegevens van de ingelogde persoon uit de `Klantinteracties API`_.

#. Navigeer naar de tab *Variabelen*, en daarbinnen naar de tab *Gebruikersvariabelen*.

#. Voeg een variabele toe met de naam "Profiel prefill" en datatype ``Lijst (array)``.

#. Klik op het potlood-icoontje in de kolom "Prefill" van de gebruikersvariabele. Je
   kan nu de opties instellen:

    * **Plugin**: Communicatievoorkeuren (Klantinteracties API)
    * **API-groep**: Selecteer een groep die aangemaakt is door een beheerder.
    * **Profielformuliervariabele**: Voorkeursadressen (de formuliercomponent).

   Sla de instellingen op.

#. Sla het formulier op.


.. _`Klantinteracties API`: https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/maykinmedia/open-klant/master/src/openklant/components/klantinteracties/openapi.yaml
