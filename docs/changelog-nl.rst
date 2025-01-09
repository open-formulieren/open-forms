.. _changelog-nl:

==============
Changelog (NL)
==============

.. note::

    This is the Dutch version of the changelog. The English version can be
    found :ref:`here <changelog>`.

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
