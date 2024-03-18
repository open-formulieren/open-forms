.. _manual_forms_basics:

===================
Formulieren beheren
===================

Een formulier bestaat (meestal) uit meerdere stappen. Een stap is in feite een
deelformulier dat we een **formulier definitie** noemen. Een **formulier**
bestaat daarom uit 1 of meerdere **formulier definities**, die de stappen van
het formulier vormen.

Een **formulier definitie** kan hergebruikt worden in andere formulieren.

Formulierenoverzicht
====================

1. Navigeer naar **Formulieren** > **Formulieren**.

U kunt vanaf deze pagina:

* De lijst van formulieren sorteren en filteren
* De details opvragen van een specifiek formulier
* Een Formulier :ref:`importeren <manual_export_import>`
* Een Nieuw formulier aanmaken
* Bulk acties uitvoeren op formulieren

  * Verwijderen
  * Kopiëren
  * Onderhoudsmodus aan zetten
  * Onderhoudsmodus uit zetten

Nieuw formulier aanmaken
========================

1. Navigeer naar **Formulieren** > **Formulieren**.
2. Klik op **Formulier toevoegen**

Er verschijnen enkele tabbladen waarmee het formulier geconfigureerd kan
worden. Onder de tabbladen zit de knop **Opslaan**. Pas als u op deze knop heeft
gedrukt wordt het formulier daadwerkelijk opgeslagen.

.. note:: Sommige formulieropties kunnen ervoor zorgen dat een tabblad wel of niet
   beschikbaar is. Uw scherm kan er dus wat anders uit zien dan in de screenshots.

Hieronder gaan we in op elk tabblad.

Formulier
---------

.. image:: _assets/form_general.png

.. note::

    Standaard staat **Actief** aangevinkt. Dit betekent dat zodra u een
    formulier opslaat, deze bereikbaar is voor iedereen.

In dit tabblad worden de algemene formulier gegevens weergegeven.

* **Uniek ID**: Een ID dat het formulier technisch identificeert maar is verder
  niet zichtbaar voor eindgebruikers.
* **Naam**: Wordt getoond aan de eindgebruiker en staat altijd bovenaan het
  formulier en het stappen overzicht.
* **URL-deel**: Dit is een deel van de URL die zichtbaar is in de navigatiebalk
  van de browser. Een *URL-deel* ``demo-formulier`` kan in de browser te zien
  zijn als ``https://klant.open-formulieren.nl/demo-formulier``.
* **Inlogopties**: Als voor een formulier ingelogd moet worden kan een van de
  beschikbare inlog opties worden aangevinkt.

  Zie ook: :ref:`configuration_authentication_index`

* **Toon voortgang**: Vink aan om de stappen bij een formulier te tonen. Typisch
  kan deze worden uitgevinkt indien er een slechts beperkt aantal stappen is.

* **Actief**: Vink aan om het formulier beschikbaar te maken voor de
  buitenwereld.

* **Onderhoudsmodus**: Vink aan om het formulier in onderhoudsmodus te zetten.
  Als het formulier in onderhoudsmodus staat, kan het formulier niet gestart
  worden en verschijnt er een melding voor de eindgebruiker. Beheerders kunnen
  het formulier blijven gebruiken.

* **Inzenden mogelijk**: Vink aan om eindgebruikers het formulier te laten
  versturen. Sommige formulieren dienen niet verstuurd te worden maar geven
  bijvoorbeeld alleen informatie of verwijzingen naar andere formulieren. In dat
  geval vinkt u deze optie uit.

* **Is afspraakformulier?**: Vink aan om het formulier als _`afspraakformulier` in te
  stellen. Afspraken dienen hiervoor :ref:`geconfigureerd <configuration_appointment_index>`
  te zijn. Wanneer deze optie inschakeld is, dan kunt u geen formulierstappen, registratie,
  product/betaling, logica of variabelen instellen.

.. note::

  Als de formuliernaam lange woorden bevat, kunt u optionele koppeltekens (`soft hyphens`_) invoeren om aan te geven waar het woord mag afgebroken worden naar de volgende regel. Op Windows vindt u deze "soft hyphens" in
  het 'Speciale tekens'-programma  en kunt u ze kopiëren/plakken naar Open Forms-velden.


.. _soft hyphens: https://en.wikipedia.org/wiki/Soft_hyphen

.. note::

  Indien een of meer **Inlogopties** zijn geselecteerd, dan verschijnt aan het
  begin van het formulier een knop om in te loggen. Echter, als er geen stappen
  in het formulier zitten die **Inloggen vereisen** (zie hieronder) dan kan het
  formulier ook gestart worden *zonder in te loggen*.


Stappen en velden
-----------------

.. image:: _assets/form_steps.png

In dit tabblad kunnen de formulier stappen worden geconfigureerd.

* U kunt een **stap toevoegen** door aan de linkerkant op het **+** icoon te
  klikken. U krijgt vervolgens de keuze om een bestaande formulier definitie
  te kiezen (die al in een ander formulier wordt gebruikt), of een nieuwe aan te
  maken.
* U kunt een **stap verwijderen** door aan de linkerkant, naast de stap naam, op
  het **vuilnisbak**-icoon te klikken. U verwijdert hiermee nooit een formulier
  definitie maar u verwijdert deze slechts als stap binnen dit formulier.
* U kunt de **volgorde van stappen wijzigen** met de **omhoog** en **omlaag**
  icoontjes voor de stap naam.
* U kunt de **details** van een stap bekijken door op de stap naam te klikken.


Het tabblad bestaat uit 2 secties: **(Herbruikbare) stapgegevens** en
**Velden**. Beide secties horen bij de huidige (rechts geselecteerde) formulier
stap.

**(Herbruikbare) stapgegevens**

* **Naam**: Wordt als stap in stappen overzicht en bovenaan het formulier.
* **URL-deel**: Dit is een deel van de URL die zichtbaar is in de navigatiebalk
  van de browser. Een *URL-deel* ``stap-1`` kan in de browser te zien
  zijn als ``https://klant.open-formulieren.nl/demo-formulier/stap-1``.
* **Inloggen vereist**: Geeft aan of voor deze stap inloggen is vereist. Zodra
  een formulier één of meerdere stappen bevat waarvoor inloggen is vereist, dan
  moet een *Inlogoptie* aangevinkt zijn onder het tabblad *Formulier*.

**Velden**

In deze sectie kunt u velden (ook wel componenten genoemd) naar de formulier
stap slepen en configureren. Kijk voor alle mogelijkheden naar het overzicht van
:ref:`formulier velden <manual_form_fields>` en naar de
:ref:`voorbeelden <manual_examples>`.

Bevestiging
-----------

In dit tabblad kan de bevestiging, die te zien is na het afronden van het
formulier, worden aangepast alsmede de e-mailbevestiging die gestuurd word naar
de indiener van het formulier.

U kunt in zowel de bevestigingspagina als de e-mailbevestiging gebruik maken
van variabelen. Uitleg hierover vind u bij :ref:`manual_templates`

Sjabloon bevestigingspagina
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In het veld **Inhoud** kan een tekst worden opgemaakt die wordt getoond na
het indienen van het formulier. Indien dit veld leeg wordt gelaten zal de
globale **Bevestigingspagina tekst** gebruikt worden.

Bevestigingsmailsjabloon
~~~~~~~~~~~~~~~~~~~~~~~~

In het veld **Inhoud** kan een tekst worden opgemaakt die gebruikt wordt in de
e-mailbevestiging. Het **Onderwerp** van de email kan ook worden opgegeven.

U moet in de optie **E-mailsjabloon** expliciet opgeven welk e-mailsjabloon
gebruikt wordt voor de e-mailbevestiging. U kunt er ook voor kiezen om geen
e-mailbevestiging te versturen.


Registratie
-----------

In dit tabblad kunt u aangeven op welke manier uw inzendingen moeten worden
geregistreerd. Alle inzendingen komen altijd binnen bij Open Formulieren zelf
maar kunnen daarnaast doorgezet worden naar een extern systeem.

Zie ook: :ref:`configuration_registration_index`


Knopteksten
-----------

U kunt de knoppen die standaard in het formulier getoond worden een ander label
geven. De waarden die hier staan overschrijven de labels die globaal zijn
geconfigureerd.


Product en betaling
-------------------

Hier kunt u een **Product** kiezen dat gekoppeld is aan het formulier. Het
product bevat een prijs die gebruikt kan worden als betaald moet worden voor
het product. Betaling kan ingesteld worden door de juiste **Betaalprovider** te
selecteren.

Ten slotte kunt u ervoor kiezen om de prijs van het gekoppeld product te
gebruiken of logica regels op te stellen voor het bepalen van de prijs. Dit
laatste kunt u instellen onder **Prijslogica**. De **Prijslogica** volgt verder
dezelfde regels als reguliere **Logica**.

Zie ook: :ref:`configuration_payment_index`


Er zijn twee mogelijke flows om inzendingen te registreren voor formulieren waar een betaling nodig is.

1. Zodra de inzending voltooid is, wordt de inzending naar de registratiebackend gestuurd. Als het wordt betaald, wordt
   de status van de betaling in de registratiebackend aangepast. In het geval van de e-mailregistratiebackend, gebeurt
   dit door een extra (update-)e-mail te sturen, terwijl voor StUF-ZDS en ZGW registratiebackends, de betaalstatus van de zaak
   wordt aangepast.
2. De inzending wordt naar de registratiebackend gestuurd pas ná dat de betaling voltooid is.

De flow kan ingesteld worden in de **Algemene Configuratie**.

Zie ook: :ref:`configuration_general_payment_flow`


Gegevens opschonen
------------------

In dit tabblad kunt u de standaardwaarden voor het opschonen van inzendingen
overschrijven.


Logica
------

In dit tabblad kunnen regels worden gedefinieerd die, afhankelijk van de
gegevens die de gebruikers invult, zowel de inhoud als het gedrag van het
formulier kunnen wijzigen.

Logica geeft u krachtige mogelijkheden om het formulier dynamischer te maken.
Voorbeelden en uitleg over hierover vind u onder :ref:`manual_logic`.


Afspraken
---------

.. warning:: Deze manier van afspraken configureren wordt uitgefaseerd en zal in versie
   3.0 van Open Formulieren verwijderd worden. U kunt beter de
   :ref:`nieuwe afsprakenconfiguratie <afspraakformulier>` gebruiken.

Als u een formulier wilt koppelen aan een afsprakensysteem, dan kunt u hier
aangeven welke velden opgenomen moeten worden in de afspraak. Bij de meeste
afspraaksystemen zijn alle velden verplicht.

Zie ook: :ref:`configuration_appointment_index`

.. note::

   U kunt hier niet kiezen voor een gekoppeld afspraaksysteem. Deze is alleen
   globaal te configureren.


.. _manual_forms_basics_variables:

Variabelen
----------

Variabelen vormen een krachtige manier om verschillende gegevens in een formulier
bij elkaar te laten komen. U kunt :ref:`variabelen gebruiken <manual_forms_form_fields_variables_usage>`
in logica, in andere velden, of om interne gegevens op te slaan die niet voor
de eindgebruiker bedoeld zijn.

Er zijn 3 soorten variabelen:

Formuliervariabelen
~~~~~~~~~~~~~~~~~~~

Alle velden in het formulier zijn beschikbaar als variabele. De
eigenschapsnaam van een veld wordt gebruikt als variabele. Dit gebeurt
automatisch.

Gebruikersvariabelen
~~~~~~~~~~~~~~~~~~~~

Zelf te beheren variabelen die niet gekoppeld zijn aan een specifiek
formulierveld. U kunt hier bijvoorbeeld waarden opslaan die door logica worden
verkregen of uit externe koppelingen opgehaald worden.

Vaste variabelen
~~~~~~~~~~~~~~~~

Een vaste lijst met variabelen die beschikbaar zijn door het formulier heen.
Afhankelijk van het type formulier zijn variabelen wel of niet voorzien van een
waarde.

=============== ========= =========================== ====================================================================================================================
Variabele       Type      Voorbeeld waarde            Toelichting
=============== ========= =========================== ====================================================================================================================
now             datetime  ``2022-09-09 18:29:00``     Datum van vandaag. Hier zijn :ref:`verschillende weergaven <manual_templates_formatting_of_variables>` van mogelijk.
                                                      Seconden en milliseconden zijn altijd 0.
environment     string    ``production``              De waarde die tijdens de installatie gezet is als ``ENVIRONMENT``. Zie: :ref:`installation_environment_config`.
form_name       string    ``Paspoort aanvragen``      De naam van het formulier.
form_id         string    ``1c453fc8-b10f-4510-``...  Het unieke ID van het formulier.
auth            object                                Een verzameling van authenticatie gegevens. Zie hieronder.
auth.plugin     string    ``digid``                   De systeemnaam van de gebruikte authenticatie plugin.
auth.attribute  string    ``bsn``                     Kan de waarden ``bsn``, ``kvk`` of ``pseudo`` hebben.
auth.value      string    ``111222333``               De identificerende waarde in het ``attribute`` van de authenticatie plugin.
auth.machtigen  object    TODO
auth_bsn        string    ``111222333``               De waarde van ``auth.value`` indien ``auth.attribute`` als waarde ``bsn`` heeft. Anders leeg.
auth_kvk        string    ``90001354``                De waarde van ``auth.value`` indien ``auth.attribute`` als waarde ``kvk`` heeft. Anders leeg.
auth_pseudo     string    ``a8bfe7a293dd``...         De waarde van ``auth.value`` indien ``auth.attribute`` als waarde ``pseudo`` heeft. Anders leeg.
=============== ========= =========================== ====================================================================================================================
