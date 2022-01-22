===================
Formulieren beheren
===================

Een formulier bestaat (meestal) uit meerdere stappen. Een stap is in feite een
deelformulier dat we een **formulier definitie** noemen. Een **formulier**
bestaat daarom uit 1 of meerdere **formulier definities**, die de stappen van
het formulier vormen.

Een **formulier definitie** kan hergebruikt worden in andere formulieren.

Formulieren overzicht
=====================

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

  .. toctree::
     :maxdepth: 2

     ../../configuration/authentication/index

* **Toon voortgang**: Vink aan om de stappen bij een formulier te tonen. Typisch
  kan deze worden uitgevinkt indien er een slechts beperkt aantal stappen is.
* **Actief**: Vink aan om het formulier beschikbaar te maken voor de
  buitenwereld.
* **Onderhoudsmodus**: Vink aan om het formulier in onderhoudsmodus te zetten.
  Als het formulier in onderhoudsmodus staat, kan het formulier niet gestart
  worden en verschijnt er een melding voor de eindgebruiker.
* **Inzenden mogelijk**: Vink aan om eindgebruikers het formulier te laten
  versturen. Sommige formulieren dienen niet verstuurd te worden maar geven
  bijvoorbeeld alleen informatie of verwijzingen naar andere formulieren. In dat
  geval vinkt u deze optie uit.


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
e-mailbevestging. Het **Onderwerp** van de email kan ook worden opgegeven.

U moet in de optie **E-mailsjabloon** expliciet opgeven welk e-mailsjabloon
gebruikt wordt voor de e-mailbevestiging. U kunt er ook voor kiezen om geen
e-mailbevestiging te versturen.


Registratie
-----------

In dit tabblad kunt u aangeven op welke manier uw inzendingen moeten worden
geregistreerd. Alle inzendingen komen altijd binnen bij Open Formulieren zelf
maar kunnen daarnaast doorgezet worden naar een extern systeem.

.. toctree::
   :maxdepth: 2

   ../../configuration/registration/index


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

.. toctree::
   :maxdepth: 2

   ../../configuration/payment/index

Ten slotte kunt u ervoor kiezen om de prijs van het gekoppeld product te 
gebruiken of logica regels op te stellen voor het bepalen van de prijs. Dit 
laatste kunt u instellen onder **Prijslogica**. De **Prijslogica** volgt verder 
dezelfde regels als reguliere **Logica**.


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

Als u een formulier wilt koppelen aan een afsprakensysteem, dan kunt u hier
aangeven welke velden opgenomen moeten worden in de afspraak. Bij de meeste
afspraaksystemen zijn alle velden verplicht.

.. note::
  
   U kunt hier niet kiezen voor een gekoppeld afspraaksysteem. Deze is alleen
   globaal te configureren.

.. toctree::
   :maxdepth: 2

   ../../configuration/appointment/index