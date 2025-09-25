.. _examples_family_members_prefill:

========================================
Formulier met vooringevulde familieleden
========================================

In dit voorbeeld maken we een formulier met twee stappen waarbij persoonsgegevens van
partner(s) en kinderen vooringevuld worden (stap 1). In stap 2 kan je extra
gegevens opgeven voor de (geselecteerde) kinderen.

In dit voorbeeld gaan we er van uit dat u een
:ref:`eenvoudig formulier <example_simple_form>` kan maken.

.. seealso:: De :ref:`technische configuratie <configuration_prefill_family_members>` moet
   gedaan zijn om dit na te kunnen bouwen.

Formulier aanmaken
==================

Formulierstappen
----------------

We bouwen eerst de formulierstappen waar vooringevulde gegevens terecht zullen komen.

#. Maak een nieuw formulier aan:

    * Naam: Familieleden
    * Bij *Inloggen* > *Authenticatiemethode*: vink één van de (demo) DigiD
      inlogopties aan.

#. Navigeer naar de tab *Stappen en velden* en voeg een nieuwe stap toe. Kies
   *Maak een nieuwe formulierdefinitie*:

    * **Naam**: Partner en kinderen
    * Vink **Vereist authenticatie** aan.

#. Klap vervolgens de "Speciale velden" open en voeg een Partners-component toe:

    * **Label**: Partners

#. Voeg hierna een Kinderen-component toe:

    * **Label**: Kinderen
    * Vink **Schakel selectie in** aan, zodat de eindgebruiker een deel van de opgehaalde
      kinderen kan selecteren.

#. Voeg nog een nieuwe stap toe. Kies opnieuw voor *Maak een nieuwe formulierdefinitie*:

    * **Naam**: Extra informatie

#. Klap vervolgens de "Speciale velden" open en voeg een Herhalende groep-component toe:

    * **Label**: Extra kindgegevens
    * **Groepslabel**: Kind

#. Sleep een BSN-component uit *speciale velden* in de herhalende groep:

    * **Label**: BSN kind

#. Sleep een tekstveld uit *formuliervelden* in de herhalende groep:

    * **Label**: Naam

#. Voeg een Radio-component toe aan de herhalende groep:

    * **Label**: Zwemdiploma
    * **Keuzeopties**: voeg de opties "Geen", "Zwemdiploma A", "Zwemdiploma B" en
      "Zwemdiploma C" toe.

Pre-fill
--------

Nu stellen we het voorinvullen in zodat de formulierstappen de partner- en kindgegevens
van de ingelogde persoon uit de BRP ingevuld worden.

#. Navigeer naar de tab *Variabelen*, en daarbinnen naar de tab *Gebruikersvariabelen*.

#. Voeg een variabele toe met de naam "Partners prefill" en datatype ``Lijst (array)``.

#. Klik op het potlood-icoontje aan in de kolom "Prefill" van de gebruikersvariabele. Je
   kan nu de opties instellen:

    * **Plugin**: Familieleden
    * **Type**: Partners
    * **Bestemmingsvariabele**: Partners (de formuliercomponent).

   Sla de instellingen op.

#. Voeg nog een variabele toe, nu met de naam "Kinderen prefill" en opnieuw datatype
   ``Lijst (array)``.

#. Klik op het potlood-icoontje aan in de kolom "Prefill" van de gebruikersvariabele. Je
   kan nu de opties instellen:

    * **Plugin**: Familieleden
    * **Type**: Kinderen
    * **Bestemmingsvariabele**: Kinderen (de formuliercomponent).
    * Indien gewenst kan je nog extra filters instellen.

   Sla de instellingen op.

Logica
------

Tot slot is er een logicaregel nodig om de geselecteerde kinderen (stap 1) in de
herhalende groep (stap 2) met extra gegevens weg te schrijven.

#. Navigeer naar de tab *Logica*.

#. Voeg een logicaregel toe, en kies voor "Geavanceerd". Als trigger vul je ``true`` in,
   zodat de regel altijd geëvalueerd wordt.

#. Voeg een actie toe, kies voor *Synchroniseer variabelen* en klik de *Instellen* knop
   aan.

#. Stel de actie in:

    * **Van variabele**: Kinderen (formuliercomponent in de stap "Partner en kinderen")
    * **Naar variabele**: Extra kindgegevens (herhalende groep in de stap "Extra informatie")
    * **Identificatievariabele**: BSN Kind

   In de variabelekoppelingen is nu automatisch de BSN-koppeling toegevoegd.

   Voeg nog een variabelekoppeling toe:

    * **Formuliervariabele**: Naam
    * **Attribuut**: Voornamen

   Sla de instellingen op.

#. Sla nu het formulier op - het is nu klaar om uit te voeren!
