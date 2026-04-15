.. _changelog-nl:

==============
Changelog (NL)
==============

.. note::

    This is the Dutch version of the changelog. The English version can be
    found :ref:`here <changelog>`.


3.5.0 "Kjeld" (2026-04-15)
==========================

Open Forms 3.5.0 is een feature release.

.. epigraph::

   Kjeld Nuis is een Nederlandse schaatser die in 2022 de grens van 100 km/u op
   natuurijs doorbrak. Het kostte ons `net iets langer` om snelheidsrecords te breken
   met Open Formulieren, maar uiteindelijk hebben we de herbouw van onze logica- en
   formulier-engine binnen de geplande termijn afgerond en onze doelen behaald.

Deze release bevat wijzigingen uit de alpha-versies en opgeloste bugs tot aan de
stabiele versie. Lees de release-opmerkingen aandachtig vóór het upgraden naar versie
3.5.0 en volg de onderstaande instructies.

.. note::

    Vanaf Open Formulieren 3.5 is de nieuwe renderer standaard ingeschakeld bij het aanmaken
    van een nieuw formulier. Mocht je problemen tegenkomen, dan kun je via de
    formulierinstellingen terugschakelen naar de oude renderer.

Update-procedure
----------------

Om naar 3.5 te upgraden, let dan op:

* ⚠️ Zorg dat de huidige versie 3.3.x is. We raden altijd de meest recente patch release
  aan, op het moment van schrijven zijn dit 3.4.8 en 3.3.15.
* ⚠️ Als je dit nog niet hebt gedaan, bekijk dan de handmatige actie die genoemd
  wordt in de release notes van 3.4.2.
* ⚠️ Bekijk de :ref:`gedetailleerde release notes <installation_upgrade_350>` in de
  documentatie onder **Installation** > **Upgrade details to Open Forms 3.5.0** en
  bereid je hierop voor.
* ⚠️ Controleer dat je Helm charts het script ``bin/check_celery_worker_liveness.py``
  niet gebruiken, omdat dit verwijderd is. Je kunt de nieuwe health check-mechanismen
  hier vinden: :ref:`installation_health_checks`.
* ⚠️ Logicaregels die de actie "blokkeer doorgaan naar de volgende stap" gebruiken,
  vereisen mogelijk extra aandacht.

  .. warning::

      Om de snelheidsverbeteringen in deze release te kunnen implementeren moesten we de
      instellingen van de logica-actie "blokkeer doorgaan naar de volgende stap"
      aanpassen. Je moet nu expliciet aangeven welke stap geblokkeerd moet worden.

      We hebben een automatische migratie die deze informatie toevoegt, afgeleid uit de
      bestaande logicaregel, echter kunnen we in sommige gevallen niet garanderen dat de
      toegekende stap correct is en niet tot een ander gedrag van het formulier leidt.

      Daarom vragen we formulierontwerpers/beheerders om deze gevallen handmatig te
      controleren en opnieuw te testen. We hebben hiervoor een script die een lijst
      uitdraait van de logicaregels en formulieren die gecontroleerd moet worden.

      .. code-block:: bash

          # in de container via ``docker exec`` of ``kubectl exec``:
          python /app/bin/check_disable_next_logic_action.py

      Gebruik de vlag ``--show-all`` om een volledige lijst van alle gewijzigde
      regels te tonen, ook als er geen twijfel bestaat.

* Inventariseer de formulieren die nog niet compatibel zijn met de nieuwe
  logica-evaluatie - we hebben hiervoor een script toegevoegd om problematische
  formulieren te rapporteren. Je kunt dit uitvoeren met:

  .. code-block:: bash

      # in de container via ``docker exec`` of ``kubectl exec``:
      python /app/bin/report_invalid_form_logic.py.py

  De gerapporteerde formulieren bevatten instabiele logicaregels die naar elkaar
  verwijzen. Laat formulierontwerpers deze beoordelen en corrigeren. In Open Formulieren
  4.0 wordt dit een harde eis om te kunnen upgraden.

Uitfaseringen
-------------

Deze lijst beschrijft functionaliteiten die nog niet eerder expliciet benoemd waren
als verouderd. Op `Github <https://github.com/open-formulieren/open-forms/issues/6164>`__
zie je de voortgang van alle `breaking` wijzigingen.

**Content-Security-Policy instellingen**

De omgevingsvariabele ``CSP_REPORT_ONLY`` is uitgefaseerd. De onderliggende bibliotheek
heeft haar instellingenmechanisme gewijzigd en ondersteunt nu aparte configuraties voor
afgedwongen en "alleen rapporteren" policies.

**Tekstveld locatie-instellingen**

Het afleiden van straat en gemeente is niet meer beschikbaar in de nieuwe renderer. Deze
functionaliteit wordt voorzien via het AddressNL-component. We zullen zorgen dat dit
component goed werkt zodat migreren mogelijk is, en zullen onderzoeken of we
automatische migratie-opties kunnen aanbieden.

**Oude logica-evaluatie**

In Open Formulieren 4.0 zal de "oude logica-evaluatie" verwijderd worden, enkel het
mechanisme wat in deze release geïntroduceerd is zal beschikbaar zijn. Uiteraard
behandelen we bugs in de nieuwe logica-evaluatie met hoge prioriteit om dit mogelijk te
maken zodat er een vlotte overgang is.

**Registratie-instellingen van bestanduploads**

De documenttype-instellingen bij bestanduploads zijn nu nog op basis van URLs. Dit wordt
vervangen met de selectie van een (zaaktype)catalogus en documenttypeomschrijving. De
instellingen zullen ook verhuizen naar de registratieplugininstellingen.

**Elastic APM**

De Elastic APM-client ondersteuning wordt verwijderd - we zullen vanaf 4.0 enkel Open
Telemetry ondersteunen.

**ZGW-API's-registratie**

Nu wordt standaard het zaaknummer door de Zaken API gegenereerd en gebruikt Open
Formulieren dit als publieke referentie naar de klant. Vanaf 4.0 zal Open Formulieren
standaard zelf een nummer genereren en dit als zaaknummer meesturen.

**StUF-ZDS-registratie**

Vanaf Open Formulieren 4.0 zal het KvK-vestigingsnummer bij voorkeur uit de
eHerkenning-logingegevens gehaald worden indien beschikbaar, in plaats van uit de
formuliergegevens (indien uitgevraagd).

**DigiD/eHerkenning via OIDC: Strict mode standaard aan**

Nu staat Strict mode standaard uit, vanaf Open Formulieren gaat deze standaard aan. In
strikte modus moeten bepaalde claims verplicht aangeleverd worden door de identity
provider, bijvoorbeeld:

* betrouwbaarheidsniveau
* identificatie van de handelende persoon (eHerkenning)
* service ID/UUID wanneer er sprake is van machtigen

**Haal Centraal BRP Personen bevragen 1.3**

We zullen in Open Formulieren 4 niet langer Haal Centraal BRP Personen 1.3 ondersteunen.
In de praktijk blijkt enkel versie 2.0 landelijk in productie genomen te zijn.

**Wijziging in gedrag van "Wissen als veld verborgen is"**

Vanaf 4.0 al een verborgen veld waarvan de optie om de waarde te wissen ingeschakeld is
zich anders gedragen: er zal helemaal geen waarde meer in de data beschikbaar zijn, in
plaats van de standaardwaarde/lege waarde. Dit heeft impact op formulieren met logica
die nu (onbewust) van dit gedrag afhankelijk zijn. We onderzoeken of we tools kunnen
aanbieden om het detecteren van deze situaties eenvoudiger te maken.

**Extensies**

Open Formulieren heeft extensie-mechanismen die in de praktijk nauwelijks (of zelfs
niet?) gebruikt lijken te worden. De programmeer-interfaces hiervoor worden semi-private
interfaces vanaf 4.0, wat betekent dat er brekende wijzigingen in kunnen gemaakt worden
zonder dat dit leidt tot een nieuwe major versie van Open Formulieren.

Belangrijkste verbeteringen
---------------------------

**⚡️ Performance**

We hebben veel werk verzet om de interactie van gebruikers met Open Formulieren soepeler
en sneller te maken. Dit traject is ruim een jaar geleden gestart in Open Formulieren
3.1 "Lente". Eén van de grootste bronnen van vertraging was dat er steeds communicatie
met de server nodig was om logicaregels te evalueren terwijl de gebruiker het formulier
invult.

We hebben dit opnieuw opgebouwd om zoveel mogelijk logica op de server te vermijden:

- alleen de logicaregels die relevant zijn voor de huidige formulierstap worden nog
  uitgevoerd,
- logicaregels worden automatisch gesorteerd op basis van hun onderlinge afhankelijkheden,
- er is detectie van mogelijke oneindige-lussen toegevoegd,
- de meest-toegepaste logicapatronen kunnen nu "aan de voorkant" uitgevoerd worden
  zonder dat er communicatie met de server nodig is.

Zowel de oude als de nieuwe logica-evaluatie zijn beschikbaar, en je kunt de nieuwe
variant per formulier inschakelen.

Let op: het uitvoeren van logica aan de voorkant is alleen beschikbaar als de nieuwe
renderer (sinds 3.4.0 beschikbaar) ingeschakeld is.

**🔢 Stabiele publieke referentienummers**

Bij het indienen van een formulier krijgt de eindgebruiker altijd een referentienummer.
Deze werden tot en met 3.4 typisch op willekeurige manier gegenereerd, waardoor een
kleine kans bestond dat na enige tijd een nummer opnieuw uitgegeven wordt. Nu worden
deze referenties gegarandeerd uniek gegenereerd, ook als oude inzendingen opgeschoond
worden.

Daarnaast kunnen beheerders nu ook een sjabloon voor deze referentie instellen, zodat je
je eigen voorvoegsels (in plaats van "OF-") kan gebruiken. Ook kan je er in de ZGW-API's
nu voor kiezen om het nummer door de Zaken-API of door Open Formulieren te laten
genereren.

**🔍 Monitoring en logging**

We hebben (voor nu) de laatste fase geïmplementeerd voor het bewaken en observeren van
Open Formulieren in de dienstverleningsketen, zodat eventuele verstoringen snel
gedetecteerd en opgelost kunnen worden.

Alle componenten waaruit Open Formulieren bestaat hebben nu "gezondheidcheck"-mechanismen
om te bepalen of het component functioneert. Hiermee kan automatisch een
niet-functionerende component herstart worden.

Daarbovenop ondersteunen we nu "distributed tracing" waarbij een verzoek van een
gebruiker door de hele keten gevolgd kan worden, inclusief integratie met de bestaande
logging en foutbewaking zoals Sentry.

Tot slot is de robuustheid van (audit) logs nog verder verbeterd - alle applicatielogs
worden nu naar de systeemoutput weggeschreven `en` indien gewenst, naar de databank
voor gebruiksvriendelijke inzage door beheerders.

**✉️ E-mail via de Office365 API**

Microsoft faseert hun ondersteuning voor het SMTP e-mailprotocol uit en
`is van plan <https://techcommunity.microsoft.com/blog/exchange/updated-exchange-online-smtp-auth-basic-authentication-deprecation-timeline/4489835>`_
om deze in 2027 volledig te verwijderen.

Om e-mailverzending voor Office365-gebruikers te blijven ondersteunen, kan Open
Formulieren nu e-mails versturen via de  Microsoft Graph API dankzij een bijdrage van
`Delta10 <https://www.delta10.nl/>`_.

Nieuwe functies
---------------

* Performance:

  .. note::

      We hebben in deze release de performance van de evaluatie van logicaregels
      verbeterd. Deze wijzigingen zijn standaard ingeschakeld voor nieuwe formulieren.
      Indien nodig kun je deze uitschakelen met de de featureflag "Gebruik nieuwe
      logica-evaluatie" onder de "Experimentele functionaliteit"-instellingen.

      Bij het opslaan van een formulier worden logicaregels gevalideerd en automatisch
      geordend. Als je individuele logicaregels rechtstreeks wijzigt (in de
      beheerinterface), dan kan dit tot analyses leiden die niet meer kloppen, en we
      raden dus sterk aan om niet via deze weg logicaregels te bewerken.

  - [:backend:`5861`] De logica-actie "blokkeer doorgaan naar de volgende stap" is
    aangepast - het is nu verplicht om expliciet aan te geven welke stap geblokkeerd
    moet worden. De automatische migratie kan die stap in de meeste gevallen betrouwbaar
    bepalen. Zie de opmerkingen in de update-procedure voor formulieren die handmatig
    gecontroleerd moeten worden.
  - [:backend:`2409`] Open Formulieren kan nu analyseren welke input- en
    outputvariabelen gebruikt worden in logicaregels.
  - [:backend:`2409`] Open Formulieren detecteert nu oneindige-lussen in logicaregels
    wanneer één regel afhankelijk is van het resultaat van één of meer andere regels.
    Lussen zoals ``ruleA -> ruleB -> ruleC -> ruleA`` leiden tot validatiefouten.
  - [:backend:`2409`] Logicaregels worden nu automatisch geordend wanneer je kiest voor
    de nieuwe logica-evaluatie, en toegewezen aan de relevante formulierstappen zodat op
    een bepaalde stap alleen relevante logicaregels uitgevoerd worden.
  - [:backend:`5962`] Logicaregels kunnen nu gedeeltelijk uitgevoerd worden op basis van
    resultaten uit eerdere stappen.
  - [:backend:`6038`] JsonLogic-expressies kunnen nu worden gecompileerd met
    datatype-informatie voor de frontend.
  - [:backend:`6037`] Er is nu een gedeelde jsonLogic-testsuite tussen backend en
    frontend.
  - [:backend:`6072`] Analyse van logicaregels kan nu bepalen of evaluatie op de server
    noodzakelijk is voor elke regel.
  - De logicaregels om aan de voorkant uit te voeren worden nu meegegeven naar de
    frontend.
  - [:backend:`6083`] Gedeeltelijke evaluatie van de variabele-actie toegevoegd voordat
    logicaregels naar de frontend worden gestuurd.
  - [:backend:`6109`] De velden ``completed`` en ``is_applicable`` worden niet gebruikt
    in de frontend en zijn verwijderd uit de API-endpoint.
  - [:backend:`6038`] Geborgd dat acties van het type "zet registratieplugin voor
    inzending" niet naar de frontend verstuurd worden.
  - [:backend:`6099`] Het markeren van een formulierstap als wel/niet van toepassing
    wordt nu bij alle stappen uitgevoerd.
  - [:backend:`6018`, :backend:`6129`] Het overbodige attribuut ``SubmissionStep.data``
    is verwijderd.
  - [:backend:`6143`] Documentatie toegevoegd voor ontwikkelaars over het uitlezen van
    de variabelewaarden vanuit de inzending.
  - Er is nu een metric die ontsluit hoeveel formulieren de nieuwe logica-evaluatie
    ingeschakeld hebben.
  - [:backend:`6018`] Variabelenamen opgeschoond en commentaar en docstrings bijgewerkt
    met betrekking tot de implementatie van componentzichtbaarheid.
  - [:backend:`6166`] Vergelijkingen van lijsten in JsonLogic-expressies gecorrigeerd.

* Nieuwe beheerinterface:

  .. note::

      Na veel inspanning in het ontwerp van de nieuwe beheerinterface zijn we gestart
      met de implementatiefase. Helaas is er voor dit project geen ontwikkelbudget en
      is dit gepauzeerd.

  - [:backend:`5952`] De nieuwe (v3) formulier-endpoint is toegevoegd, met minimale
    attributen.
  - [:backend:`5955`] Ondersteuning toegevoegd voor bevestigingssjablonen/-opties in het
    nieuwe endpoint.
  - [:backend:`6080`] ``uuid`` toegevoegd aan de response van het endpoint
    ``/api/v2/themes``.
  - [:backend:`5952`] Je kan nu de formulierstappen meesturen in het nieuwe
    formulier-update endpoint.
  - [:backend:`5956`] ``registration_backends`` is toegevoegd aan het nieuwe
    v3-endpoint ``/api/v3/forms/{uuid}``.
  - [:backend:`5957`] Betaalgerelateerde velden toegevoegd aan het nieuwe v3-endpoint
    ``/api/v3/forms/{uuid}``.
  - [:backend:`6119`] Ondersteuning toegevoegd voor nul stappen bij
    afsprakenformulieren in het nieuwe v3-endpoint.

* Afspraken (JCC):

  - [:backend:`5690`] De aanvullende productinformatie (HTML) is nu beschikbaar voor de
    publieke frontend.
  - [:backend:`5696`] De resterende API-calls voor de afsprakenflow zijn
    geïmplementeerd. We ondersteunen nu de REST API volledig, aangezien SOAP door JCC
    is uitgefaseerd.
  - [:backend:`5820`] Je kunt nu de teksten en vertalingen aanpassen die gebruikt
    worden in de componenten voor contactgegevens.
  - [:backend:`5691`] De limiet voor het aantal producten in afspraken is nu ontsloten
    naar de frontend.

* Monitoring en logging:

  - [:backend:`5287`] Alle containers hebben nu low-level health check-mechanismen.
  - [:backend:`5450`] Er is nu distributed tracing op basis van Open Telemetry. De
    volgende traces zijn nu beschikbaar:

    - Postgres-queries
    - Redis-queries
    - Celery-taken
    - Uitgaande verzoeken naar externe services
    - Applicatiespecifieke traces

  - [:backend:`5358`] Log-regels bevatten nu de span-/trace-ID’s voor correlatie.
  - ``TraceID`` en ``SpanID`` uit OTel worden nu vastgelegd bij Sentry-events, zodat
    correlatie tussen Sentry-events en traces/logs (bijvoorbeeld in Grafana) mogelijk is.
  - [:backend:`5351`, :backend:`6149`] De ``logevent`` module is omgebouwd zodat
    auditlogs altijd naar de systeemoutput weggeschreven worden én ook naar de database
    voor eenvoudige inzage.
  - [:backend:`6169`] De uitgaande verzoek-logs zijn nu ook gestructureerd, waarmee nu
    alle logs een consistente structuur hebben.
  - Toevoegingen van bijlagen in bestandsstappen worden nu gelogd, zodat precieze
    statistieken over bestandsuploads weergegeven kunnen worden in dashboards.

* [:backend:`5753`] Generatie van publieke referenties is nu deterministisch en
  garandeert dat er nooit dubbele referentienummers onstaan, zelfs niet als
  oude inzendingen zijn verwijderd. Beheerders kunnen een eigen sjabloon configureren.
  Voor de ZGW API’s-registratieplugin kun je nu kiezen tussen de gegenereerde
  zaaknummers en de referenties die door Open Formulieren worden gegenereerd.
* [:backend:`5972`] Ondersteuning toegevoegd voor het verzenden van e-mails via de
  Office365 Graph API.
* [:backend:`5319`] "Organization login via OpenID Connect" kan nu standaard verborgen
  worden. Gebruik de queryparameter ``authVisible=all`` om deze zichtbaar te maken in
  de publieke frontend.
* [:backend:`5820`] Endpoint voor de SDK toegevoegd om aangepaste frontend-vertalingen
  op te halen.
* [:backend:`5553`] Bij het starten van een formulier via organisatielogin namens een
  bedrijf kun je nu ook het vestigingsnummer invoeren.
* [:backend:`5216`] Het versturen van de e-mail over een betaalstatusupdate wordt nu
  overgeslagen wanneer het e-mailadres voor betaalupdates leeg is én de registratie pas
  plaats vindt bij voltooing van betaling. Dit voorkomt dubbele e-mails voor de
  backoffice.
* [:backend:`5887`] ``gor.openbareRuimteNaam`` is toegevoegd aan verblijfsadres en
  bezoekadres in StUF-ZDS.
* [:backend:`5857`] Overleden familieleden worden nu standaard niet ogehaald in de
  prefill-instellingen voor het ophalen van partners en/of kinderen.
* [:backend:`4746`] De dagelijkse probleemrapportagemail bevat nu een indicatie van de
  betreffende omgeving in het onderwerp.
* [:backend:`5977`] De logica-editor voorkomt nu dat je een component als "uitgeschakeld"
  kan markeren als het component deze eigenschap niet ondersteunt.

Beveiligingsfix
---------------

* [:cve:`CVE-2026-28803`] Kwetsbaarheid opgelost waarbij aanvallers gegevens van
  formulierinzendingen konden bekijken. Zie :ghsa:`GHSA-2g49-rfm6-5qj5` voor details en
  instructies om mogelijke inbraken te detecteren.

Bugfixes
--------

* [:backend:`5888`] Verholpen dat lege datums in een service-fetch als ``None`` werden
  weergegeven in plaats van als een lege string.
* [:backend:`5885`] Een crash opgelost in de normalisatie van datumveldwaarden wanneer
  hiervoor prefill-configuratie is ingesteld, waargenomen op de samenvattingspagina.
* [:backend:`5827`] Een registratiecrash opgelost wanneer een formulier componenten voor
  kinderen of partners bevat die verborgen zijn of onderdeel zijn van een
  niet-van-toepassing stap.
* [:backend:`5892`] Verholpen dat een componentsleutel met een ``.`` erin niet gebruikt
  kon worden als informatie voor de initiator in StUF-ZDS.
* [:backend:`5902`] Opgeschoond hoe we omgaan met vooraf ingevulde gegevens.
* [:backend:`5893`] Verholpen dat het attribuut ``amount`` van een afspraakproduct niet
  werd gezet bij het verwerken van queryparameters.
* [:backend:`5790`] Verholpen dat in de beheerinterface ten onrechte een groene
  "live"-check werd getoond voor formulieren in onderhoudsmodus.
* [:backend:`5942`] Verholpen dat mislukte Worldline-betalingen niet meer naar een
  successtatus bijgewerkt konden worden.
* [:backend:`5685`] Een oneindige lus in logicacontroles opgelost bij gebruik van de
  nieuwe renderer wanneer verborgen componenten zowel ``clearOnHide`` ingeschakeld
  hadden als een standaardwaarde.
* [:backend:`6005`] Verholpen dat invoerwaarden onbedoeld werden gewist wanneer er
  meerdere backend-logicaregels waren die invloed hadden op de zichtbaarheid van
  hetzelfde component.
* [:backend:`6007`] Verholpen dat verborgen velden niet naar de Objecten-API werden
  verstuurd bij gebruik van variabelenkoppeling (v2-configuratie). Daarnaast zijn ook
  andere plekken opgelost waar "niet-opgeslagen variabelen" niet werden meegenomen in
  het renderen van sjablonen.
* [:backend:`6014`] Verholpen dat componenten met overlappende (geneste) sleutels ten
  opzichte van hun bovenliggende component crashes in de logica veroorzaakten.
* [:backend:`6001`] Verholpen dat componenten binnen layout-componenten (veldengroep,
  kolommen) hun waarde kwijt raakten ondanks dat hun zichtbaarheid via
  backend-logicaregels ingesteld was.
* [:backend:`5980`] Verholpen dat componenten in de samenvatting/het overzicht van een
  formulier werden getoond terwijl ze via logicaregels verborgen waren.
* [:backend:`6002`] Crash opgelost in de legacy cosign-flow wanneer HEAD-verzoeken
  worden verstuurd.
* [:backend:`6016`] Crashes in StUF-ZDS-registratie opgelost die veroorzaakt werden door
  ongeldige controlekarakters uit gebruikersinvoer in XML-berichten.
* [:backend:`5950`] Verholpen dat BAG-foutresponses werden gecached.
* [:backend:`6040`] Verholpen dat velden binnen herhalende groepen onverwacht werden
  gewist.
* [:backend:`6046`] Verholpen dat het resultaat van een variabele-actie werd
  overschreven door een niet-getriggerde logica-actie op hetzelfde component die de
  zichtbaarheid beïnvloedde.
* [:backend:`6028`] Een regressie opgelost waardoor velden de eindvalidatie oversloegen
  als ze via backend-logica zichtbaar werden gemaakt.
* [:backend:`6045`] Oneindige lus in logicacontrole opgelost in de nieuwe renderer
  wanneer een herhalende groep met ``clearOnHide: false`` verborgen wordt terwijl een
  veld daarbinnen ``clearOnHide: true`` heeft.
* [:backend:`5685`] Oneindige lus in logicacontrole opgelost doordat reeds ingediende
  gegevens van een herhalende groep niet werden gebruikt in de logica-evaluatie.
* [:backend:`5967`] Verholpen dat de thema-specifieke link "terug naar de hoofdwebsite"
  en favicon niet correct werden toegepast.
* Validatiefouten in de cosign lookup-flow worden nu met correcte foutstyling getoond.
* [:backend:`6068`] Verholpen dat een bijlage mogelijk niet werd geüpload wanneer de
  zichtbaarheid van een component door een logicaregel beïnvloed werd.
* [:backend:`5701`] De ``selectboxes``-component is gecorrigeerd zodat deze niet crasht
  bij verwijdering in de admin UI als de Objects API v1 wordt gebruikt.
* [:backend:`5864`] Waarschuwingen op de formuliergeschiedenispagina worden niet langer
  getoond wanneer de applicatieversie de huidige versie is.
* [:backend:`6110`] Kapotte asset-cache verholpen door configuratie van de
  staticfiles-opslag aan te passen.
* [:backend:`5938`] Verholpen dat een onjuiste DigiD-foutmelding werd getoond wanneer
  een gebruiker een DigiD-login annuleert via de plugin "DigiD via OIDC".
* [:backend:`6140`] Een crash opgelost wanneer frontend-logica wordt gebruikt binnen
  een veldengroep in een herhalende groep.
* [:backend:`5924`] Verholpen dat validatiemeldingen de verkeerde
  (niet-toepasselijke) stappen toonden.
* Verholpen dat de rand van het beheerschermmenu niet over de volledige breedte werd
  getoond.

Projectonderhoud
----------------

* [:backend:`5879`] Detectie van componentproblemen uitgebreid en automatische fixes
  toegevoegd voor de gevonden issues.
* Inconsistente testopzetten opgeschoond.
* ``pyright`` bijgewerkt en typechecking verbeterd.
* De niet-onderhouden library bleach vervangen door de nh3 HTML-sanitizer.
* Upgrade uitgevoerd naar storybook 9.
* Backend-afhankelijkheden bijgewerkt naar de nieuwste versies:

  - protobuf
  - weasyprint
  - urllib3
  - cbor2
  - cryptography
  - Pillow
  - maykin-common
  - django-health-check
  - sqlparse
  - Django
  - lxml-html-clean
  - tornado
  - PyJWT
  - pyopenssl
  - pyasn1
  - cbor2
  - requests
  - cryptography
  - pygments
  - django-log-outgoing-requests

* Frontend-afhankelijkheden bijgewerkt naar de nieuwste versies:

  - formio-builder
  - CKEditor
  - storybook
  - copy-webpack-plugin
  - lodash en lodash-es
  - webpack

* [:backend:`5946`] Afhankelijkheid ``zgw-consumers-oas`` verwijderd en op mocks
  gebaseerde tests herschreven naar VCR-tests.
* Meer controles toegevoegd aan het PR-checklistsjabloon.
* ``npm`` verwijderd uit de productie-image, zodat deze niet beïnvloed wordt door
  kwetsbaarheden die in npm-afhankelijkheden gevonden kunnen worden.
* [:backend:`5946`] Upgrade uitgevoerd naar Django 5.2 en alle gerelateerde
  afhankelijkheden bijgewerkt.
* Geheugengebruik van flower geoptimaliseerd.
* [:backend:`5848`] De PinkRoccade-servicetests (voor HC BRP) opnieuw opgenomen met het
  nieuwe certificaat/de nieuwe sleutel.
* [:backend:`5639`] StUF-BG-tests geherstructureerd.
* Endpoints voor statische SDK-assets geoptimaliseerd.
* De parameter ``next`` wordt nu onthouden wanneer je via SSO inlogt in de
  beheerinterface.
* Postcode-component opnieuw uit de uitfasering gehaald.
* [:backend:`6066`] Locatie van de CHANGELOG verduidelijkt in stabiele
  documentatiebuilds.
* trivy-action vastgezet op een bekende goede commit naar aanleiding van
  supply-chain-aanvallen.
* Certificaten voor unittests bijgewerkt.
* Labelkoppeling voor de wysiwyg-editor op Webkit gecorrigeerd.
* Documentatie bijgewerkt voor:

  - de plugin "Communicatievoorkeuren",
  - ondersteunde versies van de Objects API.

* [:backend:`6162`] Overgestapt op individuele Utrecht NLDS community CSS-packages.

3.4.0 "Gemeentegoed" (2025-01-05)
=================================

Open Forms 3.4.0 is een feature release.

.. epigraph::

   "Gemeentegoed" benadrukt de oorsprong in de gemeentelijke wereld en de filosofie dat
   Open Formulieren van iedereen is - ofwel, gemeengoed. Naast de techniek is er in
   deze release ook hard gewerkt aan het opbouwen van de community om Open Formulieren,
   en het oprichten van "Broncodebeheer" om de gezondheid van dit Open Source project
   te borgen.

Deze release bevat wijzigingen van de alpha-versies en opgeloste bugs tot aan de
stabiele versie. Lees de release-opmerkingen aandachtig voor het upgraden naar versie
3.4.0 en volg de instructies zoals hieronder beschreven:

Update-procedure
----------------

Om naar 3.4.0 te upgraden, let dan op:

* ⚠️ Zorg dat de huidige versie 3.3.x is. We raden altijd de meest recente patch release
  aan, op het moment van schrijven is dit 3.3.9.
* Bekijk de :ref:`gedetailleerde release notes <installation_upgrade_340>` (Engels) in
  de documentatie onder **Installation** > **Upgrade details to Open Forms 3.4.0** en
  bereid je hierop voor. Heb je eigen NL DS-thema’s gebouwd, lees dan zeker de
  bovenstaande documentatie zorgvuldig door.

.. warning:: Als je dashboards hebt gebouwd op basis van de metrics-telemetrie, dan moet
   je deze bijwerken met de nieuwe namen. De nieuwe namen vind je in de documentatie.

Belangrijkste verbeteringen
---------------------------

**⚙️ Nieuwe render-engine**

We hebben een nieuwe "renderer" gebouwd die ervoor zorgt dat de formuliervelden juist
weergegeven worden, de inzendingsgegevens bijgehouden worden en (een deel van) de
formulierlogica uitvoert. Het resultaat is "snappier" gebruikersinteractie, verbeterde
toegankelijkheid en een (lichte) update van de styling, met een nauwere integratie van
NL Design System.

Zowel de oude als de nieuwe renderer zijn beschikbaar, en je kunt de nieuwe renderer
per formulier inschakelen.

We hebben nu een goede basis om een aantal langlopende bugs en gewenste verbeteringen op
te pakken.

**🗨️ Open Klant 2-integratie**

Het is nu mogelijk om communicatievoorkeuren vast te leggen in formulierinzendingen,
waardoor het eenvoudiger wordt om te voldoen aan de WMEBV-eisen. Hoewel het patroon
generiek is en klaar is voor ondersteuning van andere leveranciers, ondersteunen we
op dit moment specifiek Open Klant 2.

Uitfaseringen
-------------

Zie de :ref:`gedetailleerde release notes <installation_upgrade_340>` (Engels).

Gedetailleerde wijzigingen
--------------------------

**Nieuwe functies**

* Nieuwe render-engine:

  - Alle resterende bestaande componenten zijn geïmplementeerd in de nieuwe renderer.
  - Performance is verbeterd.
  - De toegankelijkheid van de ``textfield``- en ``textarea``-componenten met
    ``showCharCount: true`` is verbeterd.
  - In de e-mailverificatie-flow krijg je nu feedback dat het e-mailadres is bevestigd.
  - Een aantal custom validatiefoutmeldingen ingesteld in de backend worden nu ondersteund.
  - De standaard validatiefoutmeldingen zijn verbeterd en geven betere gebruikersfeedback.
  - Validatiefouten voor een item in een herhalende groep worden nu “bij het item” getoond
    in plaats van bij het eerste veld in het item.
  - Componenten die “alleen-lezen” zijn, worden nu op een toegankelijke manier als zodanig
    gemarkeerd in plaats van "disabled" (wat ze onzichtbaar maakte voor screen readers).
  - Een aantal gebruiksvriendelijkheidsverbeteringen zijn toegepast op componenten die
    eerder niet mogelijk waren, met name voor ``addressNL``.
  - Er is een nieuw Profiel-component voor interactie met Open Klant 2/klantinteractie-services.
  - De validatie van de geometrie op kaarten laat nu enkel locaties binnen Nederland toe.
  - De datumkiezer voor ``date``- en ``datetime``-componenten is nu toegankelijk via
    toetsenbordnavigatie en voor screenreadergebruikers.
  - Voorbereidingen toegevoegd om meer functionaliteit "op verzoek" te laden, zodat
    laadtijden verbeterd kunnen worden voor gebruikers met trage netwerkverbindingen.
  - Toegankelijkheid van ``number``-componenten met voorvoegsel en/of achtervoegsel is
    verbeterd.
  - [:backend:`5815`] Je kan nu via de command-line de nieuwe renderer in bulk
    inschakelen (voor DevOps).
  - [:backend:`5814`] Shims toegevoegd voor backwards compatibility vanwege het
    gebruik van nieuwe design tokens.

* Klantprofiel/communicatievoorkeuren:

  - Ondersteunt authenticatie en klantprofielen op basis van BSN en KVK.
  - [:backend:`5707`] Prefill-plugin geïmplementeerd om voorkeuren voor het klantprofiel
    op te halen uit klantinteractie-API’s zoals Open Klant.
  - [:backend:`5772`] API-endpoint toegevoegd om communicatievoorkeuren van het
    klantprofiel op te halen uit vooraf ingevulde gegevens.
  - [:backend:`5708`] Nieuwe ``customerProfile``-formuliercomponent toegevoegd waarin
    gebruikers hun communicatievoorkeuren kunnen opgeven.
  - [:backend:`5711`] Terugschrijven van componentgegevens naar Open Klant geïmplementeerd
    wanneer updates ingeschakeld zijn.
  - [:backend:`5795`] Algemene configuratieoptie toegevoegd voor de "klantportaal”-link
    waar gebruikers hun voorkeuren kunnen bijwerken.

* Beheerinterface:

  - [:backend:`5704`] Formulieren kunnen nu gefilterd worden op gebruikte betaalprovider.
  - [:backend:`4357`] Je kunt nu thema-specifieke favicons, organisatienamen en logo’s
    gebruiken.

* Registratie:

  - [:backend:`5643`] ``heeftAlsAanspreekpunt`` is toegevoegd aan de StUF-ZDS-registratieplugin.
  - De registratie ondersteunt nu een registratiestap per component in het formulier.
  - [:backend:`5776`] Je kunt nu elke vaste en gebruikersvariabele koppelen aan een
    StUF-ZDS-``extraElementen``-item.

* [:backend:`5683`] Het formulier-import-endpoint geeft nu de UUID van het geïmporteerde
  formulier terug.
* [:backend:`5546`] De structuur van de toegankelijkheidstoolbar is verbeterd:

  - De knop “pagina afdrukken” is verplaatst naar de footer.
  - De link “terug naar boven” is uitgelijnd met de stapnavigatie.
  - Er is een optionele visuele scheiding instelbaar tussen het formulier en de
    toegankelijkheidstoolbar.
  - De toolbar wordt nu ook weergegeven op mobiele apparaten.
  - Het ontbrekende navigatierol-label is toegevoegd.
  - De weergave kan worden aangepast met een aantal nieuwe design tokens.

* [:backend:`5598`] Het is niet langer mogelijk om je eigen inzending te medeondertekenen.

* Performance:

  - [:backend:`2409`] Gebruikersvariabelen worden nu opgeslagen bij het indienen van een
    stap, in plaats van alleen bij voltooien van de inzending. Bij problemen kan het
    oude gedrag worden hersteld met de featureflag
    ``PERSIST_USER_DEFINED_VARIABLES_UPON_STEP_COMPLETION=False``.
  - [:backend:`5747`] Rework van de opslag van inzendingsvariabelen ter voorbereiding op
    verdere verbeteringen.

* Afspraken:

  - [:backend:`5687`] Initiële structuur toegevoegd van de JCC (REST) API-afsprakenplugin,
    die uiteindelijk de SOAP-API-variant zal vervangen.
  - [:backend:`5694`] Adresgegevens voor afspraakhulplocaties zijn nu beschikbaar voor weergave.

**Bugfixes**

* [:backend:`5134`] Probleem met foute afleiding van de correcte “lege waarde” voor
  date/time/datetime-variabelen opgelost.
* Crash verholpen bij het opslaan van een formulier met een component waarvan de
  ``multiple``-eigenschap was gewijzigd.
* [:backend:`3640`] Theoretisch geval verholpen waarin een inzending gepauzeerd kon worden
  terwijl registratie bezig was of al voltooid was.
* [:backend:`5429`] Afkappen van componentlabels in het previewpaneel van de
  configuratiemodal is verholpen.
* [:backend:`5391`] Probleem opgelost waarbij inzendingslogs (onterecht) lege resultaten
  rapporteerden voor overgeslagen prefill-operaties.
* [:backend:`3544`] Probleem opgelost waarbij het opschonen van inzendingen mogelijk
  inzendingen verwijderde die nog toekomstige afspraken hadden.
* Crash verholpen in upgrade-migraties voor formuliervariabelen die naar een niet-bestaande
  component verwezen.
* [:backend:`5722`] Worldline-configuratie aangepast om rekening te houden met meerdere
  webhook key ID + secret-combinaties bij gebruik van meerdere PSPID’s.
* [Sentry#453174] Crash verholpen in het configuratieoverzicht voor ongeldige
  Worldline-merchants.
* [:backend:`5737`] Crash verholpen in de formulierbouwer-UI bij gebruik van de
  logica-actie synchroniseer variabele” in combinatie met veldengroep-componenten.
* [:backend:`5735`] Crash verholpen bij het omzetten van ruwe JSON-gegevens naar
  Python-types wanneer variabelen in bepaalde situaties niet in de database aanwezig zijn.
* [:cve:`2025-64515`] Ontbrekende logica-evaluatie vóór validatie van
  (stap)gebruikersinvoer opgelost. Zie :ghsa:`GHSA-cp63-63mq-5wvf` voor details.
* Performanceproblemen van de e-mailverificatiepagina in de beheeromgeving zijn opgelost.
* Enkele crashes verholpen die ontstonden door het inschakelen van bepaalde
  optimalisaties, met name bij:

  - Het opzoeken van het dichtstbijzijnste adres voor kaartcoördinaten.
  - Het opzoeken van adressen in de Kadaster API.
  - Het verwerken van (enkelvoudige) bestanden in de generieke registratieplugin.

* [:backend:`5757`] Crash verholpen bij het indienen van een inzendstap met bijlagen.
* [:backend:`5754`] Regressie in datum/datetime/time-opmaak in de ``extraElementen`` van
  de StUF-ZDS-registratieplugin verholpen.
* Crash verholpen in de MS Graph/SharePoint-registratieplugin doordat deze geen
  date/datetime/time-objecten naar JSON kon omzetten.
* Bug verholpen in de OpenID-library die de compatibiliteitslaag van onze legacy
  callback-endpoint stuk maakte.
* Crash verholpen bij het verwerken van gegevens van gezinsledencomponenten door een
  verschil in dataformaat tussen StUF-BG en Haal Centraal BRP Personen bevragen.
* [:backend:`5748`] Afhandeling van verschillen tussen de Haal Centraal Personen Bevragen API
  en StUF-BG bij het ophalen van gezinsleden hersteld, waardoor geldige inzendgegevens in
  kinderen- en partnercomponenten weer worden geaccepteerd.
* [:backend:`5756`] Probleem verholpen waarbij maximaal één kind werd opgehaald bij
  kinderen-prefill bij gebruik van StUF-BG.
* [:backend:`5765`] Probleem opgelost die was geïntroduceerd in de 3.3.3-beveiligingsfix,
  waardoor geldige waarden niet werden geaccepteerd in radio-, select- en
  selectboxes-componenten met opties afkomstig uit een variabele.
* Verholpen dat de Token Exchange-extensie niet meer werkte door het rework van de OpenID-library.
* [:backend:`5770`] Crash verholpen bij het registreren van gegevens voor de
  ``partners``-component met StUF-ZDS.
* [:backend:`5778`] Crashes verholpen tijdens registratie met de Objects API wanneer er
  date- of datetime-velden in een herhalende groep zitten.
* [:backend:`5784`] Probleem opgelost met Worldline-creditcardbetalingen waarbij de
  autorisatiemode niet op ``SALE`` stond.
* [:backend:`5733`] Verholpen dat uitgaande verzoeken voor de Generieke JSON-registratie
  niet werden gelogd.
* [:backend:`5803`] Workaround toegepast voor date/time/datetime-objecten in inzendgegevens
  die automatisch volgens de actieve taal werden geformatteerd in Objects API V1-templates.
* [:backend:`5818`] Ontbrekend ``bsn``-element toegevoegd in StUF-BG XML-verzoek om
  kinderen op te halen.
* [:backend:`5840`] Verholpen dat ``null``-waarden naar ZGW-API’s werden gestuurd wanneer
  geneste waarden leeg waren in partner-/kindgegevens.
* [:backend:`5835`] Worldline-webhookbeheer hersteld zodat de PSPID weer wordt weergegeven.

**Projectonderhoud**

* Documentatie voor het embedden van formulieren bijgewerkt en verbeterd.
* Het verouderde privacy policy-configuratie-endpoint is verwijderd.
* Verouderde documentatie opgeschoond.
* Documentatie van compatibele versies (backend/API/SDK) bijgewerkt.
* [:sdk:`445`] Verwijzingen naar de nieuwe locaties van JS en CSS assets in de SDK bijgewerkt.
* [:backend:`5134`] Enkele bijzondere situaties opgelost waarbij evaluatie van logicaregels
  onverwachte resultaten kon opleveren door de implementatie van ``clearOnHide`` te
  corrigeren.
* Metrics zijn hernoemd om te voldoen aan OTel-naamgevingsconventies.
* zgw-consumers bijgewerkt om OAUTH2-authenticatie van services te ondersteunen.
* De container image wordt nu ook gepubliceerd naar
  `ghcr.io <https://github.com/open-formulieren/open-forms/pkgs/container/open-forms>`_.
* De onjuiste uitfaseringsmarkering op het adres-autocomplete-endpoint is verwijderd.
* Frontend-afhankelijkheden bijgewerkt met de nieuwste beveiligingsupdates (invloed op
  ontwikkeltooling).
* Upgrade uitgevoerd naar mozilla-django-oidc-db met verbeterde type-annotaties.
* ``openforms.authentication``, ``openforms.data_removal`` en ``openforms.emails`` toegevoegd
  aan type-checkerconfiguratie in CI.
* Documentatie toegevoegd over het ontwikkelen van UI-componenten.
* Beveiligingsupdates toegepast voor:

  - Django
  - brotli
  - fonttools
  - urllib3

* [DH#817] Extra logging en foutinformatie toegevoegd voor het geval de
  Worldline-betaalflow faalt.
* (Ontwikkel)frontend-afhankelijkheden bijgewerkt met de nieuwste beveiligingsfixes.
* CI-pipeline aangepast om ook een testrun zonder ``assert``-statements uit te voeren.
* Linterregel ingeschakeld die controleert op mogelijke bugs door verwijderde
  ``assert``-statements.
* Gebruik van ``typing.cast`` verboden via een linterregel.
* Optie ingeschakeld in de typechecker om een fout te geven wanneer foutonderdrukking
  niet langer nodig is.
* CI-pipeliens opgeschoond door gebruik te maken van eigen herbruikbare Github actions.
* Generatie van Docker Hub imagebeschrijvingen is nu een volledig zelfstandig script,
  uitgevoerd met ``uv``.
* VCR-checklisttemplate bijgewerkt en een hulpscript toegevoegd om alle benodigde
  containers te starten met geïsoleerde poortnummers.
* [:backend:`5739`] Verouderde migraties verwijderd/opgeschoond.
* Verouderde fix-/diagnosescripts verwijderd.
* Overgestapt op django-test-migrations voor het testen van migraties.
* NLX verwijderd uit de repo-submodules.
* Workaround toegevoegd om applicatieworkerprocessen te recyclen bij geheugenlekken.
  We onderzoeken de onderliggende oorzaken.

3.3.0 "Donders mooi" (2025-10-02)
=================================

Open Forms 3.3.0 is een feature release.

.. epigraph::

   Donders mooi – een uitdrukking uit het Twents dialect voor ‘enorm mooi’. Met deze naam
   verwijzen we naar de oorsprong van Open Formulieren bij Dimpact en benadrukken we
   de samenwerking met dit samenwerkingsverband, dat gevestigd is in Enschede, de grootste
   stad van Twente.

Deze release bevat wijzigingen van de alpha-versies en oplossingen tot aan de
stabiele versie. Lees de release-opmerkingen aandachtig voor het upgraden naar versie 3.3.0
en volg de instructies zoals hieronder beschreven:

Update-procedure
-----------------

Om naar 3.3.0 te upgraden, let dan op:

* ⚠️ Zorg dat de huidige versie 3.2.x is. We raden altijd de meest recente patch
  release aan, op het moment van schrijven is dit 3.2.4.

* ⚠️ Plan een upgrade tijdslot in i.v.m de onderstaande waarschuwingen.

* ⚠️ Een automatische Ogone-to-Wordline merchantmigratie vereist unieke merchant-PSPIDs. Dit wordt
  automatisch gecontroleerd *vóór* het uitvoeren van de upgrade, maar we raden aan om het check script in
  oudere patch-versies uit te voeren ter voorbereiding.

.. warning:: De Open Telemetry SDK is standaard ingeschakeld. Als er geen endpoints zijn geconfigureerd
   om systeemtelemetrie naar te versturen, dan raden we aan om de deployment aan te passen als volgt:
   ``OTEL_SDK_DISABLED=true`` (dit is een omgevingsvariabele).

   Als je dit niet doet dan zullen er waarschuwingen in de container-logs verschijnen. De applicatie blijft wel
   werken zoals gewoonlijk.

.. warning:: Plan de upgrade in in daluren. Sommige databasemigraties zullen volledige
   tabellen locken en/of kunnen een lange tijd in beslag nemen afhankelijk van de hoeveelheid aan data.
   Er zijn verschillende benchmarks uitgevoerd om een idee te krijgen van de duur.

   ============================================================= ============== ========
   Resource(s)                                                   Aantal records Duur
   ============================================================= ============== ========
   Emailberichten + logs                                          50.000         ~30s
   Inzendingen, inzendingsvariabelen                              150.000        ~2s
   Inzendingen, inzendingsvariabelen                              13.600.000     ~10min
   Authenticatie-infos                                            1.500          ~0,1s
   Authenticatie-infos                                            230.000        ~2s
   ============================================================= ============== ========

.. warning::

   In deze release, hebben we de interne datatype-informatie herzien. Om te borgen
   dat de invoergegevens van bestaande inzendingen correct weergegeven worden, moeten de
   overeenkomstige variabelen bijgewerkt worden. We hebben hiervoor een los script voorzien,
   zodat het apart uitgevoerd kan worden. Op grote omgevingen kan de uitvoering van dit script
   lang duren.

   .. code-block:: bash

       # in de container via ``docker exec`` of ``kubectl exec``:
       python /app/bin/fix_submission_value_variable_missing_fields.py

    Zie onze benchmarks om een indicatie te krijgen van de doorlooptijd:

    ====================== ========
    Aantal inzendingen     Duur
    ====================== ========
    7.000                  3,5min
    ====================== ========

.. warning::

    Voor de email- en bevestigingssjablonen, en de registratiebackends, is de manier
    waarop data berekend wordt herzien. In het geval van conflicterende variabelen,
    (vaste, component- en gebruikersvariabelen), zullen de vaste variabelen "winnen".
    Voorheen hadden de component- en gebruikersvariabelen hogere prioriteit.
    Validatie zorgt er al voor dat het niet mogelijk is om eigen variabelen toe te voegen die al voorkomen
    in de statische variabelen. Dit is echter niet van toepassing op oudere formulieren en nieuwe vaste
    variabelen die we eventueel toevoegen.

Belangrijkste verbeteringen
---------------------------

**💳 Worldline (vervanging voor Ogone) ondersteuning**

De Worldline-betalingsprovider is nu beschikbaar, ter vervanging van Ogone Legacy. Ogone Legacy
wordt door Worldline op 31 december 2025 stopgezet.

De migratie is zoveel mogelijk geautomatiseerd om het overstappen eenvoudig te maken. Je kan deze
migratie al voorbereiden in oudere versies van Open Formulieren (vanaf 3.2.3 en 3.1.8). Meer informatie
is beschikbaar in de documentatie.

**🗺️ Kaartlagen en geavanceerde interacties**

Het is nu mogelijk om eigen achtergrondlagen toe te voegen aan kaartmateriaal, bijvoorbeeld om BAG-
locaties te tonen bovenop de achtergrondlaag. De standaardset met achergrondlagen is ook uitgebreid.

Daarnaast toont de samenvatting-PDF nu een afbeelding van de kaart, inclusief de eigen kaartlagen, in
plaats van de tekstuele weergave van de coördinaten.

**🚸 Kinderen-component met prefill**

De vorige minor release had al ondersteuning toegevoegd voor het partners-component,
deze release voegt ondersteuning toe voor het nieuwe kinderen-component. Zoals het partners-component,
kan bij het nieuwe kinderen-component informatie zoals initialen, achternaam, BSN en
geboortedatum van een kind opgeslagen of getoond worden.

Ook hier kunnen de gegevens vooringevuld worden met de familieleden-prefillplugin die eerder geïntroduceerd
werd (met Haal Centraal BRP Personen bevragen en StUF-BG). Met deze functionaliteit is de verbeterde
ondersteuning voor familieleden compleet.

**📈 Applicatiestatistieken**

We hebben doorgebouwd bovenop eerdere "observability"-verbeteringen. De applicatie produceert nu
periodiek statistieken "over zichzelf" (o.a duur van HTTP-verzoeken, aantal actieve verzoeken, maar
ook het aantal formulieren, inzendingen en gebruikersbijlage-metadata).

Deze statistieken worden uitgezonden op basis van de Open Telemetry standaard en integreren mooi in
bestaande monitoring- en visualisatie-tooling.

Gedetaileerde wijzigingen
-------------------------

**Nieuwe functies**

* [:backend:`4480`] Verbeterde ondersteuning voor achtergrond- en tegellagen in het kaartcomponent:

  * [:backend:`5253`] De BRT (grijs, pastel, water) achtergrondlagen zijn nu
    standaard beschikbaar in een Open Formulieren-installatie.
  * [:backend:`5251`] Het identificatieveld van de kaart achtergrondlagen wordt
    nu automatisch ingevuld op basis van het label.
  * [:backend:`4951`] Het kaartcomponent in de samenvatting-PDF is nu een afbeelding in plaats
    van een tekstuele weergave.
  * [:backend:`5618`] WMS-kaartlagen worden getoond op de kaartafbeelding in de samenvatting-PDF.

* [:backend:`5359`] Ondersteuning voor het kinderen-component:

  * [:sdk:`825`] Kinderen-component toegevoegd en de digest-email bijgewerkt.
  * [:backend:`5268`] Registratieplugins ondersteunen nu het ``children`` component-type.
  * [:backend:`5269`] Je kan nu gegevens van een ``children`` component gebruiken als bron voor de
    gegevens van een herhalende groep, met het nieuwe "Synchroniseer variabelen" logica-actietype. Hiermee
    kan je extra gegevens per kind opgeven.

* [:backend:`4879`] Ondersteuning voor de Worldline-betalingsprovider:

  - Ondersteuning voor Worldline's ``variant`` and ``descriptor`` velden.
  - De betalingsreferentie wordt gegenereerd door Open Formulieren, vergelijkbaar met de Ogone plugin.
  - Automatische migratie van Ogone-merchants waar mogelijk.
  - Webhookconfiguratie (indien geconfigureerd in een oudere patch release) wordt
    automatisch gemigreerd.
  - Er is een bulk-actie in de beheeromgeving om de formulieren met Ogone-betaalprovider te migreren
    naar de equivalente Wordline-configuratie.

* [:backend:`5478`] Additionele Yivi documentation toegevoegd.
* [:backend:`5428`] eIDAS (OIDC) LoA-Levels bijgewerkt.
* [:backend:`5515`] Yivi-attribuutgroepen hebben nu een systeem-gegenereerde unieke identificatie.
* [:backend:`5515`] Het is nu mogelijk om Yivi-attribuutgroepen te exporteren en importeren.
* [:backend:`5479`] De eIDAS (via OIDC) configuratie is nu vergemakkelijkt - het is nu mogelijk
  om te kiezen welke claims een BSN en/of Pseudo ID bevatten.
* [:backend:`5419`] Prefill plugins toegevoegd voor de nieuwe Yivi and eIDAS authenticatiebackends.

* [:backend:`3999`] Ondersteuning voor Open Telemetry statistieken. Alle beschikbare statistieken
  en details zijn te vinden in de "Observability" documentatie.

* [:backend:`5095`] Indien er geauthenticeerd is via OpenID Connect (DigiD, eHerkenning, organization),
  zal bij het voltooien van een inzending de gebruiker uitgelogd worden bij de identity provider.
* [:backend:`5133`] Optie toegevoegd om de nieuwe *experimentele* renderer in te schakelen.
* [:backend:`5268`] "Partners Roltype" en "Partners omschrijving" registratie-instellingen
  toegevoegd voor de ZGW APIs en StUF-ZDS registratieplugins.
* [:backend:`5060`] Redis Sentinel wordt nu ondersteund als high availability strategy voor de background
  jobs message broker.
* [:backend:`2324`] Een deel van de logica-engine is op de schop genomen ter voorbereiding van toekomstige
  performance-verbeteringen. Er is nu betere datatype-informatie van variabelen beschikbaar.
* [:backend:`5382`] Je kan nu "interne opmerkingen" bijhouden bij formulieren.

**Bugfixes**

* [:backend:`5225`] De placeholders van datum- en datumtijdcomponenten zijn nu vertaald.
* [:backend:`5615`] Probleem opgelost waarbij de ZGW API's-registratie als "mislukt" gerapporteerd werd
  wanneer er zaakeigenschappen toegevoegd worden.
* [:backend:`5507`] Mimetype detectie voor ``.msg`` bestanden opgelost.
* [:backend:`5624`] Incorrecte StUF-BG verzoeken voor kind (familieleden) prefill opgelost.
* [:backend:`5574`] Authenticatie-gerelateerde vaste variabelen zijn niet langer beschikbaar voor de
  samenvatting-PDF context.
* [:backend:`5464`] Probleem opgelost wanneer onvolledige opties gebruikt werden bij het
  genereren van een JSON-schema voor een formulier.
* [:backend:`5605`] Probleem opgelost bij het gebruik van een ontbrekende standaardwaarde
  voor de DigiD ``loa`` tijdens het inloggen.
* [:backend:`5572`] Probleem opgelost in de StUF-ZDS registratieplugin wanneer een ander
  formulier ook de familieleden-plugin geconfigureerd had.
* [:backend:`5557`] Probleem bij het verwerken van de geuploade bestandsnaam van bijlagen opgelost.
* [:backend:`5439`] Waarschuwingsmelding verwijderd voor verouderde functie om
  locatie op te halen op basis van tekstvelden.
* [:backend:`5384`] Formulierexportreferenties naar Objecten-API-groepen opgelost.
* [:backend:`5527`] Probleem opgelost waarbij niet enkel de gewijzigde stapgegevens teruggegeven werden
  in het resultaat van de logica-evaluatie.
* [:backend:`5475`] Probleem opgelost waarbij Yivi-claims met punten niet gebruikt konden worden.
* [:backend:`5271`] Probleem opgelost waarbij onterecht een melding kwam in de digest-email bij het gebruik
  van ``reduce``-operaties in formulierlogica.
* [:backend:`5481`] Probleem opgelost waarbij de formuliervariabelen niet voldoende gefilterd werden in
  sommige registratieplugins.
* [:backend:`5471`] Probleem opgelost waardoor de geavanceerde opties voor de BRP "doelbinding" bij het
  gebruik van familieleden-plugin niet getoond werden.
* [:backend:`5340`] Probleem opgelost waarbij de digest-email kon crashen als de validatie van registratie-
  plugins een onverwachte fout hadden.
* [:backend:`5454`] Het niet functioneren van de Piwik Pro debug mode opgelost.
* [:backend:`5413`] Probleem opgelost waarbij het uploaden van bijlagen met soft-hyphens in de
  bestandsnaam niet mogelijk was.
* Een crash opgelost bij het weergeven van e-mail HTML links welke dikgedrukte of
  cursieve elementen bevatten.

**Projectonderhoud**

* Een voortgangsbalk toegevoegd aan de data backfill upgrade script.
* Herbruikbare github actions toegevoegd voor i18n checks.
* Migraties opgeschoond en samengevoegd waar mogelijk.
* [:backend:`5325`] Familieledenvoorbeeld in documentatie bijgewerkt.

* [:backend:`5513`] De OTel-documentatie bijgewerkt met verschillende voorbeelden:

  - Nginx-statistieken en traces.
  - PostgreSQL-statistieken.
  - Redis-statistieken.

* [:backend:`5544`] Documentatie en voorbeelden toegevoegd over het verzamelen van
  Flower-statistieken.
* Documentatie bijgewerkt over de gebruikte SOAP-operations voor de StUF-ZDS-plugin.

* Frontend dependencies bijgewerkt:

  - @open-formulieren/formio-builder naar 0.45.0.

* Backend dependencies bijgewerkt:

  * Redis naar versie 8 bijgewerkt voor CI builds en de docker-compose configuratie.
  * zgw-consumers naar versie 1.0.
  * Django naar security release 4.2.25.
  * [:backend:`5356`, :backend:`5131`] django-digid-eherkenning van 0.22.1 naar 0.24.0.
  * [:backend:`5131`] mozilla-django-oidc-db van 0.22.0 naar 0.25.0.
  * [:backend:`5131`] django-setup-configuration van 0.6.0 naar 0.8.2.

* Het is nu mogelijk om static assets te gebruiken met een reverse proxy (nginx) in plaats
  van de applicatieserver (uwsgi) met de ``STATIC_ROOT_VOLUME`` omgevingsvariabele.
  Controleer de ``docker-compose.yml`` voor een voorbeeldconfiguratie.
* Een aantal willekeurig falen van tests geaddreseerd.
* [:backend:`5331`] Extra type checking ingeschakeld en verschillende type checking
  errors verholpen.
* Een aantal primary key velden naar bigint gemigreerd voor tabellen welke vaak gebruikt worden voor nieuwe regels/waarden.
* Verschillende best practices toegepast op de ``uwsgi`` configuratie.
* CI check toegevoegd om ontbrekende frontend-vertalingen te detecteren.
* Verouderde Ansible-deploymentvoorbeeld verwijderd.
* [:backend:`5447`] Een upgrade check toegevoegd voor het vereisen van versie 3.2.0
  voor het upgraden naar versie 3.3.0.
* Ongebruikte validatiecode verwijderd.
* Django-specifieke linterregels ingeschakeld en de foutmeldingen hiervan opgelost.

* Verschillende code-componenten vervangen met de maykin-common equivalenten.

  * PDF-generatie
  * Omgevingsinformatie in de admin
  * Serverfoutpagina
  * Systeemchecks
  * Schema hook
  * Admin-MFA-integratie
  * Admin-index-integratie

* Verouderde formulierenprijslogicamodel verwijderd.

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
    `eIDAS <https://en.wikipedia.org/wiki/EIDAS>`_-authenticatie d.m.v. het OpenID Connect-protocol. Door de
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
