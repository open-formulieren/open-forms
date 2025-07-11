.. _changelog-nl:

==============
Changelog (NL)
==============

.. note::

    This is the Dutch version of the changelog. The English version can be
    found :ref:`here <changelog>`.

3.2.0 "Nimma" (2025-07-11)
==========================

Open Formulieren 3.2.0 is een feature release.

.. epigraph::
   "Nimma" is een informele, liefkozende bijnaam voor een van de oudste
   steden van Nederland: Nijmegen. De naam wordt vaak gebruikt door de lokale
   bevolking en drukt een gevoel van trots, verbondenheid en eigen identiteit uit.
   Natuurlijk zijn we ook trots dat Nijmegen bijdraagt aan Open Formulieren.

Deze release bevat wijzigingen van de alpha-versies en oplossingen tot aan de
stabiele versie. Lees de release-opmerkingen aandachtig voor het upgraden naar versie 3.2.0
en volg de instructies zoals hieronder beschreven:

Update-procedure
-----------------

.. warning::

   The Camunda registratieplugin zal verwijderd worden in Open Formulieren 4.0. Er is geen vervanging
   gepland - neem contact op als je afhankelijk bent van deze plugin.

.. warning::

   De manier waarop data wordt gegenereerd via de Generieke JSON-registratieplugin is
   aangepast. Indien er conflicten optreden tussen vaste, component-, en gebruikersvariabelen
   worden de vaste variabelen gebruikt. Voorheen hadden in dit soort gevallen
   de component- en gebruikersvariabelen prioriteit. De validatie zorgt ervoor dat het niet mogelijk is
   om variabelen te definiëren met dezelfde sleutels als vaste variabelen. Dit geldt echter

   niet voor oudere formulieren of nieuw toegevoegde vaste variabelen.

Belangrijkste verbeteringen
---------------------------

**🔊 Verbeterde logging**

    De logging is verbeterd voor betere integratie met observatietools zoals Grafana.

**🛂 Authenticatie d.m.v. Yivi en eIDAS**

    Ondersteuning is toegevoegd voor `Yivi <https://yivi.app/>`_- en
    eIDAS <https://en.wikipedia.org/wiki/EIDAS>`_-authenticatie d.m.v. het OpenID Connect-protocol. Door de
    ondersteuning voor Yivi-athenticatie kunnen eindgebruikers nu kiezen welke informatie zij willen delen met Open Formulieren.

    Met eIDAS kunnen Europese burgers zonder DigiD (en/of BSN)
    toegang krijgen tot formulieren die deze manier van authenticatie vereisen.

**👫 Partners-component met prefill**

    Het partners-component is toegevoegd om informatie zoals initialen, achternaam en
    geboortedatum van een partner te tonen of in te voeren.

    Dit component kan vooringevuld worden door het gebruik van de nieuwe familieleden-prefillplugin.
    De familieleden-prefillplugin kan informatie opvragen vanuit "Haal Centraal BRP personen bevragen"
    (versie 2) of "StUF-BG" (versie 3.1).

**📝 JSON-schema genereren**

    Het genereren van een JSON-schema van een formulier is sinds deze release mogelijk.
    Het beschrijft de gegevens van een ingediend formulier van alle gebuikers-
    en componentvariabelen, en kan gegenereerd worden voor de Generieke JSON- of
    Objecten-API-registratieplugins. Het schema beschrijft de
    gegevensstructuur alsof deze is verstuurd met de Generieke JSON- of Objecten-API-registratieplugins.

    De schemas van componentvariabelen bevatten ook een beschrijving en eventuele validatieregels
    als deze gespecificeerd zijn in de componentinstellingen.

Gedetaileerde wijzigingen
-------------------------

**Nieuwe functies**

* [:backend:`4966`, :backend:`5285`, :backend:`5334`] Logging verbeterd voor betere
  integratie met observatietools zoals Grafana.
* [:backend:`5140`] De authenticatiemodulearchitectuur is herzien om het mogelijk
  te maken om ondersteuning toe te voegen voor nieuwe plugins gebaseerd op het OpenID
  Connect-protocol (Yivi en eIDAS).

* [:backend:`5132`] Ondersteuning toegevoegd voor authenticatie d.m.v. Yivi via het
  OpenID Connect-protocol.

    - Maakt het mogelijk om in te loggen met formulieren via DigiD, eHerkenning, of anoniem.
    - Aanvullende attributengroepen kunnen gedefinieerd worden in de Yivi configuration,
      en de relevante kunnen per form geselecteerd worden.
      Deze groepen maken het mogelijk voor eindgebruikers om, optioneel, aanvullende
      persoonlijke of bedrijfsgegevens aan te leveren.

* [:backend:`4453`] Ondersteuning toegevoegd voor authenticatie d.m.v. eIDAS via het
  OpenID Connect-protocol. Door de ondersteuning van eIDAS kunnen Europese burgers
  zonder DigiD (en/of BSN) toegang krijgen tot formulieren.

* [:backend:`5254`] Nieuwe familieleden-prefillplugin toegevoegd.

    - De gegevens kunnen worden opgehaald vanuit "Haal Centraal BRP personen bevragen"
      (version 2) of "StUF-BG" (version 3.1).
    - Partners of kinderen van de ingelogde gebruiker kunnen opgeslagen worden in een gebruikersvariabele.
    - De opgehaalde gegevens van kinderen kunnen worden gefilterd op basis van leeftijd
      en of zij overleden zijn.

* [:backend:`4944`, :backend:`5268`, :sdk:`824`] Partners-component toegevoegd.

    - Het is mogelijk om handmatig een partner toe te voegen of in te vullen met de nieuwe familieleden-prefillplugin.
    - Partners kunnen worden geregistreed via de StUF-ZDS-registratie.
    - Partnerdetails toegevoegd aan de e-mail-registratie.
    - Configuratieproblemen zullen worden toegevoegd aan de rapportage-e-mail.

* [:backend:`4923`, :backend:`5312`, :backend:`5027`] Mogelijkheid toegevoegd om een JSON-schema van een formulier te genereren.

    - Een schema kan gegenereerd worden via het tabblad **Registratie** voor
      de Generieke JSON- of Objecten-API-registratieplugins, en beschrijft de gegevensstructuur
      geproduceerd door een van deze plugins.
    - Alle gebruikers- en componentvariabelen zijn inbegrepen in het schema.
    - De componentschemas bevatten validatieregels en een beschrijving indien beschikbaar.

* [:backend:`5174`] De mogelijkheid toegevoegd om een omschrijving te configureren
  voor 'zaakbetrokkenen' (registratoren, mede-ondertekenaars of partners) in de StUF-ZDS-plugin.
* [:backend:`4877`] Ondersteuning toegevoegd voor het bijvoegen van een kopie van de
  bevestigingse-mail(s) verstuurd naar de initiator in een aangemaakte zaak
  in de ZGW API's and StUF-ZDS registraties.
* [:backend:`5193`] `exp` claim toegevoeggd aan JWT in ZGW APIs.
* [:backend:`5283`] De getoonde kolommen in de admin-formulierenlijst zijn opgeschoond
  om de UX te verbeteren.

**Bugfixes**

* [:backend:`5394`] Een crash opgelost bij het opslaan van de DigiD- of eHerkenning-
  configuratie in de admin
* [:backend:`5041`] Probleem opgelost waarbij componenten met een punt in hun sleutel
  niet toegevoegd werden aan de data van de Generieke JSON-registratie.
* Probleem verholpen waarbij verborgen selectievakjes component onderdeel was van de
  ingediende data als leeg object.
* [:backend:`5326`] Fouten door onvoldoende geheugen tijdens de e-mailopschoning opgelost.
* Het niet matchen van de standaardwaarde van de ``clearOnHide``-optie met de frontend opgelost.
* [:backend:`5303`] Springende gebruikersvariabelen vanwege de auto-sort opgelost.
* [:backend:`4401`] Oneindige omleiding door fout-geconfigureerde OIDC-authenticatiebackend opgelost.
* [:backend:`5300`] Een regressie met geneste ingediende data in de vorige alpha release
  is opgelost.
* [:backend:`4933`] Ontbrekende Cosign v2-informatie toegevoegd voor registratie-e-mailsjablonen.
* [:backend:`5245`] Een incorrecte variablekoppeling-configuratie wanneer er meerdere
  registratiebackends beschikbaar zijn voor een form is opgelost.
* [:backend:`5214`] Het niet gebruiken van de employee ID binnen de authenticatiecontext wanneer de organization-via-OIDC-plugin gebruikt wordt, is opgelost.
* [:backend:`5238`] De volgorde van de formulierversies in de versiegeschiedenis is opgelost.
* [:backend:`5263`] Dubbele encodering van data in de Generieke JSON-registratieplugin
  is opgelost.
* [:backend:`5202`] Afspraakinformatie onder het onderdeel inzendingen in de admin is verwijderd.
* [:backend:`5207`] Twee bugs omtrent de referentielijsten-integratie zijn opgelost:

    - Het genereren van JSON-schemas voor componenten die de referentielijsten als databron
      gebruiken in de Generieke JSON-registratieplugin is opgelost.
    - Het tonen van actieve items van niet-actieve tabellen voor componenten die referentielijsten
      als databron gebruiken is opgelost.
* De ‘verstuur als lijst'-instelling voor de Objecten-API-variabele-opties die beschikbaar was
  voor alle componenten is opgelost.
* De ‘koppel aan geometrie-veld’-instelling voor de Objecten-API-variabele-opties die bescikbaar
  was voor alle componenten is opgelost.
* [:backend:`5181`, :backend:`5235`, :backend:`5289`] Incorrecte ``null`` waarde in
  componenten zijn opgelost.
* [:backend:`5243`] Niet-bestaande variablen die meegenomen werden in de 'verstuur als lijst'
  optie van de Generieke JSON-registratie en Objecten-API plugins zijn opgelost.
* [:backend:`5239`] ``kvkNummer``-attribuut dat niet werd meegestuurd in ZGW API's
  registraties is opgelost.
* [:backend:`4917`] De backwards-compatibility-problemen van de herziene formuliernavigatie zijn opgelost.
  Zie `de SDK storybook <https://open-formulieren.github.io/open-forms-sdk/?path=/docs/developers-upgrade-notes-3-1-0--docs>`_ for gedetaileerde upgrade-documentatie.
* Probleem opgelost waarbij API spec-strings met het format 'uri' een lege waarde hadden
  als standaardwaarde.
* HTML sanitization van design tokens opgelost.

**Projectonderhoud**

* [:backend:`5252`] JSON Dump-plugin hernoemd naar Generieke JSON-registratie.
* [:backend:`5179`, :backend:`5221`, :backend:`5139`] Het aanmaken en gebruik van gegevensstructuren is geoptimaliseerd.
* [:backend:`5407`] Een melding toegevoegd in de 3.1.0 upgradeprocedure over
  mogelijk lange upgradetijd vanwege een migratie.
* De meeste bugbear linter-regels zijn ingeschakeld.
* OAS-checks zijn vervangen in de CI door een herbruikbare workflow.
* Oudere release notes zijn gearchiveerd.
* Voorbereidende werkzaamheden voor de migratie naar django-upgrade-check.
* Overgestapt van bump2version naar bump-my-version.
* Overgestapt naar ruff van black, isort en flake8.
* Een script is toegevoegd dat ervoor zorgt dat "fix"-scripts correct functioneren.
* Willekeurig falende tests zijn opgelost.
* Type checking opgelost.
* Pyupgrade linter-regels ingeschakeld.

* Backend dependencies bijgewerkt:

    - django naar 4.2.23.
    - urllib3 naar 2.5.0.
    - requests naar 2.32.4.
    - vcrpy naar 7.0.0.
    - h11 naar 0.16.0.
    - httpcore naar 1.0.9.
    - tornado naar 6.5.
    - zgw-consumers naar 0.38.0.
    - celery naar 5.5.0.
    - django-privates naar 3.1.1

* Frontend dependencies bijgewerkt:

    - @open-formulieren/design-tokens naar 0.59.0.
    - @open-formulieren/formio-builder naar 0.41.1.

3.1.0 "Lente" (31 maart 2025)
=============================

Open Formulieren 3.1.0 is een feature release.

.. epigraph::

    In deze release hebben we wat zaadjes geplant die wat tijd nodig hebben om volledig
    te ontbloeien en daarna kunnen we hiervan de vruchten plukken. Hier en daar kan je
    wel al wat bloemetjes van verbeteringen zien!

    De lente is typisch een periode in het jaar die weer meer licht en geluk brengt, en
    we hopen dat deze nieuwe versie dat ook doet.

Deze release bevat de wijzigingen uit de alpha-versie en de fixes die zijn toegepast tot
de stabiele versie. VOORDAT je update naar 3.1.0, lees de release-opmerkingen
zorgvuldig door en volg onderstaande instructies.

Update-procedure
----------------

Om naar 3.1.0 te upgraden, let dan op:

* ⚠️ Zorg dat je minimaal op versie 3.0.1 zit. We raden altijd de meest recente patch
  release aan, op het moment van schrijven is dit 3.0.6.

* ⚠️ Controleer het aantal log records voor het toepassen van de upgrade. Via [:backend:`4931`]
  is er een migratie toegevoegd die log records verwerkt en kan zorgen voor een langere
  verwerkingstijd.

* We raden aan om de scripts ``bin/report_component_problems.py`` en
  ``bin/report_form_registration_problems.py`` uit te voeren om bestaande problemen in
  formulieren te detecteren. Deze worden automatisch verholpen tijdens de upgrade, maar
  het is verstandig om een beeld te hebben van welke formulieren/formulierdefinities
  aangepakt gaan worden zodat je deze achteraf kan controleren. Deze scripts zijn ook
  beschikbaar in de laatste 3.0.x patch release, dus je kan ze uitvoeren vóór je gaat
  updaten.

* We hebben wat UX-aanpassingen gedaan in de SDK (op basis van NL Design System).
  Hierdoor moet je mogelijks extra waarden van design-tokens opvoeren als je een eigen
  thema gebruikt.

* We hebben nooit bewust ondersteuning voor HTML in veldlabels en tooltips toegevoegd.
  Doordat er wat extra HTML-escaping toepepast wordt kan het zijn dat sommige HTML nu
  geëscaped wordt. Ons advies blijft om **GEEN** HTML te gebruiken op plaatsen waar geen
  WYSIWYG-editor gebruikt wordt.

Waar mogelijk hebben we automatische upgrade-checks toegevoegd die problemen detecteren
vóór er database-wijzigingen doorgevoerd worden.

Belangrijkste verbeteringen
---------------------------

**📒 Referentielijsten-API-integratie**

Je kan nu gebruik maken van de `Referentielijsten-API`_. In deze API kan je centraal
(vaste) lijsten beheren zoals wijken, communicatiekanalen, de weekdagen en meer!

In Open Formulieren kan je deze lijsten gebruiken als bron voor de keuzeopties bij de
"Keuzelijst"-, "Selectievakjes"- en "Radio"-componenten zodat je deze niet steeds hoeft
per-formulier bij te houden.

**📦 JSON-dump-registratieplugin**

We hebben een nieuwe registratieplugin toegevoegd waarbij je eenvoudig een setje
variablen en hun waarde in JSON-formaat naar een externe API kan opsturen.
Formulierbouwers kunnen instellen welke variabelen ingestuurd moeten worden en naar
welke service, en vervolgens worden de waarden, wat metadata en een schema die de
gegevens beschrijft opgestuurd zodat deze eenvoudig verwerkt kunnen worden.

Deze plugin werkt goed samen met ESB's die de gegevens (verder) transformeren en kan
een eerste stap zijn richting strikte contracten via de Objecten-registratie.

**🗺 Kaartmateriaal**

We zijn de functionaliteiten van het kaartcomponent aan het uitbreiden zodat deze
breder inzetbaar wordt.

Meest opvallend is dat er nu extra geometrieën beschikbaar zijn naast de "marker" (die
eenvoudig latitude en longitude registreert), namelijk *lijn* en *veelhoek*, wat toelaat
om complexere situaties goed te beschrijven.

Formulierbouwers kunnen nu ook alternatieve achtergrondlagen instellen - standaard wordt
de BRT-laag van het Kadaster gebruikt, maar nu kan je ook luchtfoto's (bijvoorbeeld)
gebruiken, én je kan je eigen achtergrondlagen instellen.

.. note:: Er wordt nog gewerkt aan verdere kaartverbeteringen voor de gebruiker.

**♿️ Toegankelijkheid**

Toegankelijkheid borgen is een continu verbeterproces, maar in deze release konden we hier
weer wat extra aandacht aan geven. De inzendings-PDF is nu een stuk toegenkelijker en
informatiever. Daarnaast is de formuliernavigatie voor eindgebruikers bijgewerkt - op
basis van onderzoek en gebruikerstesten uitgevoerd door andere organisaties. Met name de
gebruikerservaring op breedbeeldschermen is hiermee verbeterd.

Ook voor de formulierbouwers zijn er een aantal (kleine) UX-verbeteringen waardoor het
eenvoudiger wordt om formuliervariabelen te beheren en er meer overzicht moet komen.

.. _Referentielijsten-API: https://referentielijsten-api.readthedocs.io/en/latest/

**Nieuwe functies**

* [:backend:`5137`] Je kan nu de naam instellen van de request header die bij "Haal
  Centraal Personen bevragen" voor het ``OIN`` gebruikt wordt.
* [:backend:`5122`] De beschrijvingen voor de Ogone legacy ``TITLE``- en ``COM``-parameters
  zijn duidelijker gemaakt.
* [:backend:`5074`] Je kan nu de geselecteerde waarden van een "Selectievakjes"-component
  als lijst van waarden opsturen in de Objecten-API- en JSON-dump-registratieplugins,
  in plaats van sleutel-waarde object.
* UX: de formuliervariabelen zijn nu per stap gegroepeerd.

* [:backend:`5047`] De inzendings-PDF is nu toegankelijker:

    - Er is nu een tekstalternatief voor het logo.
    - Er is nu een semantische relatie tussen het label van het formulierveld en de
      opgegeven waarde.
    - De PDF toont nu "Geen informatie ingevuld" bij velden die niet ingevuld zijn door
      de gebruiker.

* [:backend:`4991`, :backend:`4993`, :backend:`5016`, :backend:`5107`, :backend:`5106`,
  :backend:`5178`] Je kan nu gebruik maken van de Referentielijsten-API. De tabellen
  worden gebruikt voor de keuzeopties in de "Keuzelijst"-, "Selectievakjes"- en "Radio"-
  componenten.

    - Je kan nu referentielijsten als "keuzeopties" gebruiken, waarbij je een service en
      tabel moet aanduiden.
    - Er is al support voor de toekomstige meertaligheid.
    - Beheerders worden geattendeerd op (binnenkort) vervallen tabellen en/of items.

* [:backend:`4518`] Prefill-acties zijn nu inzichtelijk in de inzendingslogs.
* Performance bij het ophalen en verwerken van formuliergegevens is verbeterd.
* [:backend:`4990`] Registratievariabelen tonen nu altijd bij welke registratieplugin ze
  horen.
* [:backend:`5093`, :backend:`5184`] Het beheren van lijst/object-variabelen is nu wat
  gebruiksvriendelijker.
* [:backend:`5024`] De configuratievalidatie op de ZGW-API's en Objecten-API is iets
  minder strikt gemaakt zodat Open Formulieren met een grotere groep leveranciers
  gebruikt kan worden.
* [:backend:`2177`] De kaartcomponenten hebben nu ``GeoJSON`` als waarde in plaats van
  ``[latitude, longitude]``-coordinaten, zodat we lijnen en veelhoeken kunnen
  ondersteunen.
* [:backend:`4908`, :backend:`4980`, :backend:`5012`, :backend:`5066`] De
  JSON-dump-registratieplugin is nieuw.

    - Formulierbouwers kiezen welke variabelen verstuurd worden.
    - De formulier- en componentinstellingen zorgen ervoor dat het schema van elke
      variabele automatisch gedocumenteerd wordt.
    - Er is een groep van vaste metadatagegevens en extra variabelen kunnen als metadata
      opgenomen worden.

* [:backend:`4931`] De inzendingsstatistieken zijn bijgewerkt en de datumfilters werken
  nu zoals verwacht. Je kan nu ook bepalen welke soort gegevens geëxporteerd worden.
* [:backend:`4785`] De eHerkenning-metadatageneratie is bijgewerkt conform de laatste
  versie van de standaard.
* [:backend:`4510`] De overzichtspagina toont nu de validatiefouten van de backend.

**Kleine security-verbeteringen**

Deze verbeteringen zijn gericht op impact-beperking indien een malafide medewerker
probeert misbruik te maken van hun beheerdersrechten.

* Beheerders kunnen niet langer de inzendings-PDF vervangen door een ander bestand in
  de beheerinterface.
* SVG-afbeeldingen die in de beheerinterface geüpload worden (bijvoorbeeld voor logo's
  en favicons), worden nu geschoond van schadelijke elementen.
* De formuliervoorvertoning in de beheeromgeving past nu extra client-side HTML-escaping
  toe. Dit gebeurde al door de backend en er is nooit een probleem geweest in de
  publieke UI.

**Bugfixes**

* [:backend:`5186`, :backend:`5188`] Problemen opgelost waarbij soms te veel auditlogs
  aangemaakt werden of prefillgegevens ontbraken in de logs.
* [:backend:`5155`] Probleem opgelost waarbij de ``initial_data_reference``-parameter
  niet behouden werd bij het veranderen van de taal in een gestart formulier.
* [:backend:`5151`] Verborgen kaartcomponenten verzoorzaken nu geen validatiefouten meer.
* [:backend:`4662`, :backend:`5147`] Fouten opgelost in "Selectievakjes"-component waarbij
  "Minimum aantal aangevinkte opties" ingesteld is:

    - Er is nu geen validatiefout meer als geen opties aangevinkt zijn in een
      niet-verplicht component.
    - Het pauzeren van een formulier is nu mogelijk als er geen opties aangevinkt zijn.

* [:backend:`5157`] Probleem opgelost waarbij onterecht een waarschuwing over
  mede-ondertekenenvertalingen getoond werd.
* [:backend:`5158`] Probleem opgelost waardoor het verwijderen van een ZGW-API-groep niet
  mogelijk was.
* [:backend:`5142`] Probleem opgelost waarbij het leek also een logicaregel onklaar
  gemaakt werd wanneer een (selectievakjes-)component verwijderd werd.
* [:backend:`5105`] Klein styling probleem opgelost in de beheeromgeving waarbij de
  asterisk voor verplichte velden bovenop dropdowns zichtbaar was.
* [:backend:`5124`] Probleem opgelost waarbij verborgen en alleen-lezen prefill-velden
  validatiefouten veroorzaakten.
* [:backend:`5031`] Probleem opgelost waarbij sommige configuratieopties ontbraken in de
  Objecten-API configuratie voor variabelekoppelingen.
* [:backend:`5136`] Probleem opgelost waarbij de Dienstcatalogus met oude certificaten
  gengenereerd werd.
* [:backend:`5040`] Probleem opgelost in de formulierlogica waar bij het verwijderen van
  de eerste actie het erop leek dat een andere actie verwijderd werd.
* [:backend:`5104`] Probleem opgelost waarbij "Radio"-componenten ``null`` kregen als
  ``defaultValue``.
* [:backend:`4871`] Probleem opgelost in de beheerinterface waarbij sommige
  validatiefouten (variabelekoppelingen in Objecten-API en DMN-mapping) niet getoond
  werden.
* [:backend:`5039`] Probleem opgelost waarbij sommige validatiefouten niet getoond
  werden in de e-mailregistratieplugin.
* [:backend:`5090`] Probleem opgelost waarbij het "Foutmeldingen aangeraden velden"-
  component doorgaan naar de volgende stap blokkeerde.
* [:backend:`5089`] Probleem opgelost waarbij de query parameters van de service-fetch
  operatie onbedoeld omgezet werden van ``snake_case`` naar ``camelCase``.
* [:backend:`5077`, :backend:`5084`] Performanceproblemen opgelost bij het laden van
  logicaregels in de admin en het opslaan van formulierstappen en -definities met een
  groot aantal componenten.
* [:backend:`5037`] Probleem opgelost waarbij datums niet correct geformatteerd werden
  in de inzendings-PDF.
* [:backend:`5058`] Race-conditie en oorzaak van database-errors opgelost bij het
  bewerken van formulieren, oorspronkelijk veroorzaakt door :backend:`4900`.
* [:backend:`4689`] Probleem met verwerking van bijlagen in herhalende groepen opgelost.
* [:backend:`5034`] Crash opgelost bij het proberen valideren van "object ownership" in
  de Objecten-API-registratieplugin.
* Foute configuratie voor het end-to-end testen van de AddressNL-component opgelost.
* Fouten in het ``registration`` management command opgelost.
* Styling-probleem opgelost in dropdowns die gereset kunnen worden.
* Probleem opgelost waarbij een upgrade check niet correct de upgrade blokkeerde.
* [:backend:`5035`] Probleem opgelost waarbij dubbele waarden in de sjabloon-versie van
  de Objecten-API-registratieplugin verstuurd werden.
* [:backend:`4825`] Probleem opgelost waarbij de digest-email onterecht prefill-fouten
  rapporteerde.

**Projectonderhoud**

* "Flakiness" van tests verminderd.
* Oude upgrade checks zijn verwijderd.
* Een aantal instellingen kunnen nu met environment variabelen gedaan worden:
  ``AXES_FAILURE_LIMIT`` en ``EMAIL_TIMEOUT``.
* [:sdk:`76`] Het inladen van frontend gebeurt nu met ESM modules wanneer de browser
  dit ondersteunt.
* [:backend:`4927`] System check toegevoegd voor ontbrekende configuratie op
  niet-verplichte serializer-velden.
* [:backend:`4882`] Documentatie voor het gebruik van django-setup-configuration toegevoegd.
* [:backend:`4654`] De squashed migrations zijn opgeschoond.
* Backend dependencies bijgewerkt:

    - playwright naar 1.49.1.
    - typing-extensions naar 4.12.2.
    - django naar 4.2.18.
    - django-digid-eherkenning naar 0.21.0.
    - kombu naar 5.5.
    - jinja2 naar 3.1.6.
    - tzdata naar 2025.1.

* Frontend dependencies bijgewerkt:

    - undici naar 5.28.5.
    - @utrecht/components naar 7.4.0.
    - @open-formulieren/design-tokens naar 0.57.0.
    - storybook naar 8.6.4.

3.0.0 "Heerlijkheid" (9 januari 2025)
=====================================

Open Formulieren 3.0.0 is een feature release.

.. epigraph::

   Tot de 19e eeuw was het platteland van Noord- en Zuid-Holland verdeeld in honderden
   kleine juridisch-administratieve eenheden, de "heerlijkheden". De huidige gemeenten
   kunnen worden beschouwd als een soort opvolgers van de voormalige heerlijkheden. De
   release-naam weerspiegelt de invloed van verschillende grote en kleinere gemeenten
   op deze release. Dit is ook een "heerlijke" release met veel nieuwe functies,
   verbeteringen en opschoningen.

Deze release bevat de wijzigingen uit de alpha-versie en de fixes die zijn toegepast tot
de stabiele versie. VOORDAT je update naar 3.0.0, lees de release-opmerkingen
zorgvuldig door en bekijk de instructies in de documentatie onder
**Installation** > **Upgrade details to Open Forms 3.0.0**

Belangrijkste verbeteringen
---------------------------

**📥 Objecten-API prefill**

Als je informatie over aanvragen/producten voor gebruikers opslaat in de Objecten-API,
kun je deze gegevens nu gebruiken om een formulier vooraf in te vullen. Bijvoorbeeld om
een product (object) opnieuw aan te vragen of te verlengen. Gegevens uit het gekoppelde
object worden vooraf ingevuld in formuliervelden en -variabelen.

Daarnaast kan je ervoor kiezen om het bestaande object bij te werken in plaats van een
nieuw object aan te maken tijdens registratie!

We hebben een voorbeeld toegevoegd bij :ref:`Prefill voorbeelden <examples_objects_prefill>`.

**🖋️ Verbeteringen in mede-ondertekeningsflow (fase 1)**

We bieden nu een veel intuïtievere gebruikerservaring voor het mede-ondertekenen van een
formulier. Gebruikers hoeven minder te klikken, en we hebben veel frictie in dit proces
weggenomen.

Daarbovenop bieden de nieuwe configuratie-opties voor mede-ondertekening meer controle
over de inhoud van e-mails en schermen - van de uitnodiging om te mede-ondertekenen tot
de bevestigingspagina die de gebruiker ziet.

**💳 Krachtigere prijsberekeningen**

We hebben het eenvoudiger en intuïtiever gemaakt voor formulierenontwerpers om
dynamische prijslogicaregels te definiëren. Deze maken nu deel uit van de reguliere
logicaregels. Hierdoor kan je complexere berekeningen uitvoeren en communiceren met
externe systemen om prijsinformatie op te halen!

**🛑 Limiteren van het aantal inzendingen**

Je kunt nu een maximumaantal inzendingen voor een formulier instellen. Dit is handig in
situaties met beperkte beschikbaarheid/capaciteit, zoals lotingen of aanmeldingen voor
evenementen. Daarnaast hebben we de statistieken uitgebreid zodat je succesvol
geregistreerde inzendingen kunt exporteren.

**🤖 Automatische technische configuratie**

We leveren enkele tools voor infrastructuurteams (devops) die Open Formulieren
implementeren. Hiermee is het mogelijk configuratie-aspecten te automatiseren die eerder
enkel via de beheerinterface konden worden ingesteld.

We breiden de mogelijke configuratie-aspecten nog verder uit, dus blijf op de hoogte!

**🚸 Verbeteringen in gebruikerservaring**

We hebben talloze verbeteringen aangebracht in de gebruikerservaring bij registratie en
de configuratie van prefill-plugins! Je hoeft geen URL's uit andere systemen meer te
kopiëren - in plaats daarvan selecteer je de relevante optie in een dropdown. Deze
dropdowns hebben nu ook een zoekveld zodat je eenvoudiger door tientallen of honderden
beschikbare zaaktypen kan navigeren.

Bovendien worden formuliervariabelen nu gegroepeerd per soort variabele en worden ze met
meer context weergegeven, én er is een zoekveld in de dropdown.

Volledig overzicht van wijzigingen
----------------------------------

**Breaking changes**

* [:backend:`4375`] De omgevingsvariabele ``DISABLE_SENDING_HIDDEN_FIELDS`` voor de
  Objecten-API is verwijderd.
* Automatisch patchen van ``cosign_information`` template-tag verwijderd.
* [:backend:`3283`] Een aantal functionaliteiten die als verouderd gemarkeerd waren zijn
  nu verwijderd (lees de instructies in de documentatie onder **Installatie** >
  **Upgrade-details naar Open Forms 3.0.0** voor alle noodzakelijke details):

    - ``registration_backend`` en ``registration_backend_options`` velden uit formulier.
    - Conversie van ``stuf-zds-create-zaak:ext-utrecht`` naar ``stuf-zds-create-zaak``
      tijdens import.
    - Conversie van Objecttype-URL naar UUID bij import.
    - Compatibiliteitslaag voor styling/design tokens.
    - Formio-component voor wachtwoorden.
    - Conversie van FormIO-vertalingen in het oude formaat.
    - De verouderde OIDC-callback-endpoints zijn nu standaard uitgeschakeld (maar wel
      nog beschikbaar).
    - De migratieprocedure voor registratiebackends is gedocumenteerd.
    - Objecten-API- en ZGW-API-groepvelden niet-nullable gemaakt waar nodig.
    - API-endpoints gebruiken nu consistent kebab-case in plaats van snake_case.
    - Ongebruikt filtergedragop het formulierdefinities-endpoint is verwijderd.
    - Legacy machtigen-context verwijderd.
    - De oude afsprakenmodule is verwijderd.
    - Tijdelijke bestanduploads bij inzending niet-nullable gemaakt.
    - Conversie van formulierstap-URL naar formulierstap-UUID verwijderd.
    - Naam formulierdefinitie alleen-lezen gemaakt.

* [:backend:`4771`] Prijslogicaregels zijn verwijderd en vervangen met reguliere
  logicaregels.

**Nieuwe functies**

* [:backend:`4969`] De UX van de formulier-editor is verbeterd:

    - Het tabblad basisconfiguratie groepeert nu gerelateerde velden en maakt het
      overzichtelijker door ze samen te vouwen.
    - Het verschil tussen de configuratie van de introductiepagina en de velden voor
      introductietekst op de startpagina is duidelijker gemaakt.

* Registratieplugins:

    * [:backend:`4686`] Alle configuratie-opties voor registratieplugins worden nu
      in een modal met verbeterde en consistente UI ingesteld.

    * E-mail:

        * [:backend:`4650`] Je kan nu de ontvanger(s) van de registratiemail instellen
          via een formuliervariabele.

    * Objecten-API:

        * [:backend:`4978`] De configuratie van "variabelen-mapping" is nu de
          standaardinstelling - dit heeft geen invloed op bestaande formulieren.
        * De technische configuratiedocumentatie is bijgewerkt.
        * [:backend:`4398`] Je kan ervoor kiezen om een object bij te werken wanneer de
          inzending verwijst naar een bestaand object - in plaats van een nieuwe record
          aan te maken. Bij het bijwerken wordt gevalideerd dat de ingelogde gebruiker
          de "eigenaar" is van het object door hun identificatie (zoals BSN) te
          vergelijken met een attribuut in het object.
        * [:backend:`4418`] Je kunt nu individuele onderdelen van het component
          "addressNL" koppelen aan attributen in het objecttype.

    * ZGW-API's:

        * [:backend:`4606`] Verbeterde gebruikerservaring van de plugin:

          - Alle dropdowns/comboboxen hebben nu een zoekveld.
          - Je kan nu selecteren welke catalogus moet worden gebruikt, zodat alleen
            relevante zaak- en documenttypen worden weergegeven.
          - Tijdens de registratie selecteert de plugin automatisch de juiste versie van
            het zaak- en documenttype.
          - URL-gebaseerde configuratie kan nog steeds worden gebruikt, maar zal in de
            toekomst verwijderd worden.

        * [:backend:`4796`] Je kan nu een product uit het geselecteerde zaaktype kiezen
          dat op de aangemaakte zaak wordt ingesteld.
        * [:backend:`4344`] Je kunt nu selecteren welke Objecten-API-groep moet worden
          gebruikt in plaats van "de eerste" te gebruiken.

    * StUF-ZDS:

        * [:backend:`4319`] Je kan nu een aangepaste documenttitel opgeven via de
          componentconfiguratie.
        * [:backend:`4762`] De mede-ondertekenaar-ID (BSN) wordt nu opgenomen in de
          aangemaakte zaak.

* Prefill-plugins:

    * Objecten-API:

        * [:backend:`4396`, :backend:`4693`, :backend:`4608`, :backend:`4859`] Je kunt
          nu een variabelen prefillen met gegevens van een object uit de Objecten-API
          (ook wel "product-prefill" genoemd):

            - Je stelt in waar het object moet opgehaald worden en van welk objecttype
              het is.
            - Je stelt in welke attributen van het object aan welke formuliervariabelen
              toegekend moeten worden.
            - Als je voor de registratie ook de Objecten-API gebruikt, dan kan je de
              instellingen en koppelingen hieruit overnemen om dubbel werk te voorkomen.
            - Je kan instellen of en hoe de "eigenaar"-controle uitgevoerd wordt om
              misbruik te voorkomen.

        * Er is documentatie toegevoegd voor product-prefill in de gebruikershandleiding.

* Betalingsplugins:

    * Ogone:

        * [:backend:`3457`] Je kan nu extra parameters voor de financiële
          afdeling/gebruiker instellen via de ``TITLE`` en ``COM`` parameters.

* [:backend:`4785`] De eHerkenning-metadatageneratie is bijgewerkt om te voldoen aan de
  nieuwste versie(s) van de standaard.
* [:backend:`4930`] Het is nu mogelijk om geregistreerde inzendingsmetadata te exporteren
  via de formulierenstatistieken in de beheeromgeving.
* [:backend:`2173`] Het kaartcomponent ondersteunt nu het gebruik van een andere
  achtergrond-/tegellaag.
* [:backend:`4321`] Formulieren kunnen nu een inzendingslimiet hebben. De UI toont
  passende meldingen wanneer deze limiet is bereikt.
* [:backend:`4895`] Metadata toegevoegd aan uitgaande bevestigings- en
  mede-ondertekeningsverzoek-e-mails.
* [:backend:`4789`, :backend:`4788`, :backend:`4787`] ``django-setup-configuration`` is
  toegevoegd om Open Formulieren programmatisch te configureren met verbindingsparameters
  voor Objecten- en ZGW-API's. Je kan een configuratiebestand laden via het
  ``setup_configuration`` management-commando. Zie :ref:`installation_configuration_cli`
  voor meer details.
* [:backend:`4798`] De bevestigingsschermen/overlays hebben nu consistent dezelfde UX/UI,
  en de UX en toegankelijkheid van overige modals is verbeterd.
* [:backend:`4320`] De mede-ondertekeningsflow en de bijbehorende teksten zijn verbeterd
  en flexibeler gemaakt:

    - Er zijn nu sjablonen voor de inhoud van de bevestigingsschermen specifiek voor
      mede-ondertekening, met de optie om een 'nu mede-ondertekenen'-knop toe te voegen.
    - Er zijn nu sjablonen voor de onderwerpregel en inhoud van de bevestigings-e-mail
      specifiek voor mede-ondertekening.
    - Wanneer links worden gebruikt in de e-mail met mede-ondertekeningsverzoeken, kan
      de mede-ondertekenaar nu direct doorklikken zonder een code in te voeren om de
      inzending te bekijken.
    - De standaardsjablonen zijn bijgewerkt met betere teksten en instructies.

* [:backend:`4815`] De minimale verwijderlimiet voor inzendingen is nu 0 dagen, zodat
  inzendingen op dezelfde dag verwijderd kunnen worden.
* [:backend:`4717`] Verbeterde toegankelijkheid voor site-logo, foutmeldingen en PDF-documenten.
* [:backend:`4719`] Toegankelijkheid verbeterd in postcodevelden.
* [:backend:`4707`] JsonLogic-widgets kunnen nu groter gemaakt worden.
* [:backend:`4720`] Toegankelijkheid verbeterd voor de skiplink en het PDF-rapport.
* [:backend:`4764`] Je kan nu de prijs van een inzending uit een formuliervariabele afleiden.
* [:backend:`4716`] Vertalingen toegevoegd voor formuliervelden en bijbehorende
  verbeteringen in foutmeldingen.
* [:backend:`4524`, :backend:`4675`] Selecteren van een formuliervariabele is nu
  gebruiksvriendelijker. Variabelen worden logisch gegroepeerd en er is een zoekveld
  toegevoegd.
* [:backend:`4709`] De foutfeedback bij onverwachte fouten tijdens het opslaan van een
  formulier in de formulier-editor is nu duidelijker.

**Bugfixes**

* [:backend:`4978`] Onbedoelde HTML-escaping in de samenvatting-PDF en bevestigingsee-mail
  bij bijlagen is opgelost.
* [:backend:`4978`] Het incorrect markeren van een formulieren als geometrie-attribuut
  in de Objecten-API-registratie is opgelost.
* [:backend:`4579`] Fout opgelost waarbij verkeerde stappen werden geblokkeerd wanneer
  logica de optie "inschakelen vanaf stap" gebruikt.
* [:backend:`4900`] Fout opgelost met opnieuw koppelen van inzendingswaardevariabelen
  voor herbruikbare formulierdefinities.
* [:backend:`4795`] Probleem opgelost waarbij het niet altijd mogelijk was om ``.msg``-
  en ``.zip``-bestanden te uploaden.
* [:backend:`4825`] Probleem opgelost waarbij irrelevante prefill-fouten als probleem
  gerapporteerd werden wanneer een formulier meerdere inlogsoorten ondersteunt.
* [:backend:`4863`] Crash opgelost wanneer organisatie-login wordt gebruikt voor een formulier.
* [:backend:`4955`] De verkeerde volgorde van lat/lng-coördinaten in Objecten-API- en
  ZGW-API-registratie is rechtgezet.
* [:backend:`4821`] Fout opgelost waarbij e-maildigest BRK/addressNL-configuratieproblemen
  verkeerd rapporteerde.
* [:backend:`4949`] De sluitknop van modals is nu zichtbaar in donkere modus (beheeromgeving).
* [:backend:`4886`] Probleem opgelost waarbij bepaalde varianten van CSV-bestanden op Windows
  niet konden geüpload worden.
* [:backend:`4832`] Een fout waardoor bepaalde objecttype-eigenschappen niet beschikbaar
  waren in de registratievariabelen-mapping is opgelost.
* [:backend:`4853`, :backend:`4899`] Fout opgelost waardoor het niet mogelijk was om
  optionele configuratievelden weer leeg te maken.
* [:backend:`4884`] Fout opgelost die ervoor zorgde dat onbedoeld een variabele
  aangemaakt werd voor "Foutmeldingen aangeraden velden"-componenten.
* [:backend:`4874`] Ontbrekende scripts in de Docker image zijn toegevoegd.
* [:backend:`3901`] Status van mede-ondertekening hield geen rekening met logica/dynamisch
  gedrag van de mede-ondertekeningscomponent.
* [:backend:`4824`] Formuliervariabelen worden nu correct gesynchroniseerd met de inhoud
  van de formulierdefinities na het opslaan.
* Fout in Django-admin formulierveldopmaak opgelost.

**Projectonderhoud**

* Documentatie bijgewerkt met betrekking tot frontend-toolchains en Formio search
  strategies (hypothesis).
* [:backend:`4907`] Installatiedocumentatie voor ontwikkelaars verbeterd.
* Storybook-setup verbeterd om beter aan te sluiten bij het daadwerkelijk gedrag in de
  Django-admin.
* [:backend:`4920`] Migraties opgeschoond en samengevoegd waar mogelijk.
* Open Formulieren versie-upgradepadcontroles ontdubbeld.
* Vervallen domeinen voor VCR-tests gedocumenteerd.
* Stabiliteit in testsuite verhoogd.
* [:backend:`3457`] Type checking toegevoegd op de hele payments-module.
* Migratietests verwijderd die afhankelijk waren van echte modellen.
* Waarschuwingen in DMN-componenten aangepakt.
* Ongebruikte ``uiSchema``-eigenschap uit registratievelden verwijderd.
* Overbodige ``.admin-fieldset``-styling verwijderd.
* Aangepaste helptekst-styling verwijderd en standaard Django-styling toegepast.
* ``summary``-tag implementatie vervangen door ``confirmation_summary``.
* Stories voor de variabeleneditor zijn bijgewerkt.
* [:backend:`4398`] De implementatie van het ``TargetPathSelect``-component is opgeschoond.
* [:backend:`4849`] Template voor releasevoorbereiding bijgewerkt met ontbrekende VCR-paden.
* API-endpoints bijgewerkt met correct taalgebruik (NL -> EN).
* [:backend:`4431`] Backwards compatibility voor addressNL-mapping verbeterd en
  Objecten-API v2-handler herzien.
* Recursieproblemen opgelost in search strategies voor Formio componenten.
* Herhaalde code voor betalings-/registratieplugin-configuratieopties is nu vervangen
  met een abstractie.
* CI-workflow opgeschoond.
* [:backend:`4721`] Screenshots in documentatie voor Prefill en Objecten-API-handleiding
  zijn bijgewerkt.
* Frontend-dependencies bijgewerkt:

    - MSW is geüpdate naar 2.x.
    - RJSF verwijderd.
    - Storybook bijgewerkt naar 8.4.

* Backend-dependencies bijgewerkt:

    - Jinja2 geüpgraded naar 3.1.5.
    - Django geüpgraded naar 4.2.17 patch-versie.
    - Tornado-versie bijgewerkt.
    - lxml-html-cleaner geüpgraded.
    - Waitress geüpgraded.
    - django-silk-versie bijgewerkt voor compatibiliteit met Python 3.12.
    - Trivy-action bijgewerkt naar 0.24.0.
