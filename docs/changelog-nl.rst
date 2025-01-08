.. _changelog-nl:

==============
Changelog (NL)
==============

.. note::
    
    This is the Dutch version of the changelog. The English version can be 
    found :ref:`here <changelog>`.


3.0.0 "Heerlijkheid" (8 januari 2025)
=====================================

Open Formulieren 3.0.0 is een feature release.

.. epigraph::

   Tot de 19e eeuw was het platteland van Noord- en Zuid-Holland verdeeld in honderden kleine juridisch-administratieve 
   eenheden, de "heerlijkheden". De huidige gemeenten kunnen worden beschouwd als een soort opvolgers van de voormalige 
   heerlijkheden. De release-naam weerspiegelt de invloed van verschillende grote en kleinere gemeenten op deze 
   release. Dit is ook een "heerlijke" release met veel nieuwe functies, verbeteringen en opschoningen.

Deze release bevat de wijzigingen uit de alpha-versie en de fixes die zijn toegepast tot de stabiele versie.
VOORDAT u upgradet naar 3.0.0, lees de release-opmerkingen zorgvuldig door en bekijk de instructies in de documentatie 
onder **Installation** > **Upgrade details to Open Forms 3.0.0**


Belangrijkste verbeteringen
---------------------------

**📥 Objecten API prefill**

Als u informatie over aanvragen/producten voor gebruikers opslaat in de Objecten API, kunt u deze gegevens nu gebruiken 
om een formulier vooraf in te vullen. Bijvoorbeeld om een product (object) opnieuw aan te vragen of te verlengen. 
Gegevens uit het gekoppelde object worden vooraf ingevuld in formulier-velden en variabelen.

Daarnaast kunt u ervoor kiezen om het bestaande object bij te werken in plaats van een nieuw object aan te maken 
tijdens registratie!

Een voorbeeld is te vinden in :ref:`Prefill voorbeelden <examples_objects_prefill>`.

**🖋️ Verbeteringen in mede-ondertekeningsflow (fase 1)**

We bieden nu een veel intuïtievere gebruikerservaring voor het mede-ondertekenen van een formulier. Gebruikers hoeven 
minder te klikken, en we hebben veel frictie in dit proces weggenomen.

Daarbovenop bieden de nieuwe configuratie-opties voor mede-ondertekening meer controle over de inhoud van e-mails en 
schermen - van de uitnodiging om te mede-ondertekenen tot de bevestigingspagina die de gebruiker ziet.

**💳 Krachtigere prijsberekeningen**

We hebben het eenvoudiger en intuïtiever gemaakt voor formulierenontwerpers om dynamische prijslogica-regels te 
definiëren. Deze maken nu deel uit van de reguliere logica-regels. Hierdoor kunt u complexere berekeningen uitvoeren en 
communiceren met externe systemen om prijsinformatie op te halen!

**🛑 Limiteren van het aantal inzendingen**

U kunt nu een maximumaantal inzendingen voor een formulier instellen. Dit is handig in situaties met beperkte 
beschikbaarheid/capaciteit, zoals lotingen of aanmeldingen voor evenementen. Gerelateerd daaraan hebben we de 
statistieken uitgebreid zodat u succesvol geregistreerde inzendingen kunt exporteren.

**🤖 Automatische technische configuratie**

We leveren enkele tools voor infrastructuurteams (devops) die Open Formulieren implementeren. Hiermee is het mogelijk 
configuratie-aspecten te automatiseren die eerder enkel via de beheerinterface moesten worden ingesteld.

We breiden de mogelijke configuratie-aspecten nog verder uit, dus blijf op de hoogte!

**🚸 Verbeteringen in gebruikerservaring**

We hebben talloze verbeteringen aangebracht in de gebruikerservaring bij registratie en de configuratie van 
prefill-plugins! Geen gekopieer van URL's uit andere systemen meer - in plaats daarvan selecteert u de relevante optie 
in een dropdown.
Dropdowns ondersteunen nu een zoekveld om eenvoudiger door tientallen of honderden beschikbare zaaktypen te navigeren!

Bovendien worden formulier-variabelen nu gegroepeerd per variabel-type en de context waarin ze voorkomen, inclusief een
zoekfunctie.


Volledig overzicht van wijzigingen
----------------------------------

**Breaking changes**
 
* [:backend:`4375`] Omgevingsvariabele ``DISABLE_SENDING_HIDDEN_FIELDS`` voor Objecten API verwijderd.
* Automatisch patchen van ``cosign_information`` template-tag verwijderd.  
* [:backend:`3283`] Oude functies verwijderd (lees de instructies in de documentatie onder **Installatie** > 
  **Upgrade-details naar Open Forms 3.0.0** voor alle noodzakelijke details):  

    - ``registration_backend`` en ``registration_backend_options`` velden uit formulier.  
    - Oude API locatie-URL.  
    - Conversie van ``stuf-zds-create-zaak:ext-utrecht`` naar ``stuf-zds-create-zaak`` tijdens import.  
    - Conversie van Objecttype-URL naar UUID bij import.  
    - Backwards compatible styling.  
    - Formio-component voor wachtwoorden.  
    - Legacy FormIO vertaalconverter.  
    - Verouderde/uitgeschakelde legacy OIDC-callback-endpoints standaard verwijderd.  
    - Gedocumenteerde migratieprocedure voor registratie-backend.  
    - Objecten API- en ZGW API-groepvelden niet-nullable gemaakt waar nodig.  
    - Genormaliseerde API-eindpunten om kebab-case te gebruiken in plaats van snake-case.  
    - Onnodig filtergedrag verwijderd op het formulier-definities-eindpunt.  
    - Legacy machtigen-context verwijderd.  
    - Oude afsprakenstroom verwijderd en code aangepast aan de nieuwe.  
    - Tijdelijke bestanduploads bij inzending niet-nullable gemaakt.  
    - Conversie van formulier-stap-URL naar formulier-stap-UUID verwijderd.  
    - Naam formulier-definitie alleen-lezen gemaakt.  
* [:backend:`4771`] Prijslogica-regels verwijderd ten gunste van reguliere logica-regels.  

**Nieuwe functies**  

* [:backend:`4969`] Verbeterde UX van de formulier-editor:  

    - Het tabblad basisconfiguratie groepeert nu gerelateerde velden en maakt het overzichtelijker door ze samen te 
      vouwen.  
    - Configuratie van de introductiepagina verduidelijkt ten opzichte van de velden voor introductietekst.  
* Registratie-plugins:  

    * [:backend:`4686`] Alle configuratie-opties voor registratie-plugins worden nu consequent beheerd in een modaal 
      met verbeterde UX.  

    * E-mail:  

        * [:backend:`4650`] De e-mailregistratie-plugin ondersteunt nu het instellen van de ontvanger met 
          formulier-variabelen.  
    * Objecten API:  

        * [:backend:`4978`] De configuratie van "variabelen-mapping" is nu de standaardinstelling - dit heeft geen 
          invloed op bestaande formulieren.  
        * Technische configuratiedocumentatie voor Objecten API bijgewerkt.  
        * [:backend:`4398`] U kunt nu een bestaand gerefereerd object bijwerken in plaats van een nieuw record aan te 
          maken.  
          Bij het bijwerken van het object wordt het BSN van de geauthenticeerde gebruiker geverifieerd aan de hand van 
          de bestaande objectgegevens.  
        * [:backend:`4418`] U kunt nu individuele delen van het component "addressNL" koppelen.  
    * ZGW API's:  

        * [:backend:`4606`] Verbeterde gebruikerservaring van de plugin:  

          - Alle dropdowns/comboboxen hebben nu een zoekveld.  
          - U kunt nu selecteren welke catalogus moet worden gebruikt, zodat alleen relevante zaak- en documenttypen 
            worden weergegeven.  
          - Tijdens de registratie selecteert de plugin automatisch de juiste versie van een zaak- en documenttype.  
          - URL-gebaseerde configuratie kan nog steeds worden gebruikt, maar wordt in de toekomst verwijderd.  
        * [:backend:`4796`] U kunt nu een product selecteren dat op de aangemaakte zaak wordt ingesteld, vanuit het 
          geselecteerde zaaktype in de ZGW API's registratie-plugin.  
        * [:backend:`4344`] U kunt nu selecteren welke Objecten API-groep moet worden gebruikt in plaats van 
          "de eerste" standaard te gebruiken.  
    * StUF-ZDS:  

        * [:backend:`4319`] U kunt nu een aangepaste documenttitel opgeven via de componentconfiguratie.  
        * [:backend:`4762`] De medeondertekenaar-ID (BSN) wordt nu opgenomen in de aangemaakte zaak.  
* Prefill-plugins:  

    * Documentatie toegevoegd voor product-prefill in gebruikershandleiding.  

    * Objecten API:  

        * [:backend:`4396`, :backend:`4693`, :backend:`4608`, :backend:`4859`] U kunt nu een variabele configureren die 
          vooraf wordt ingevuld vanuit de Objecten API ("product-prefill"):  

          - Het is mogelijk om individuele eigenschappen van het objecttype toe te wijzen aan specifieke 
            formulier-variabelen.  
          - Om duplicatie in de configuratie te vermijden, kunt u de configuratie kopiëren van een geconfigureerde 
            registratie-backend.  

* Betalingsplugins:  

    * Ogone:  

        * [:backend:`3457`] Aangepaste ``title`` en ``com`` parameters kunnen nu worden gedefinieerd in de Ogone 
          betalingsplugin.  
* [:backend:`4785`] Bijgewerkte eHerkenning-metadata-generatie om te voldoen aan de nieuwste standaardversie(s).  
* [:backend:`4930`] Het is nu mogelijk om geregistreerde inzendingsmetadata te exporteren via de 
  formulierenstatistieken in de adminpagina. Dit kan worden gebaseerd op een specifieke datumbereik.  
* [:backend:`2173`] Het kaartcomponent ondersteunt nu het gebruik van een andere achtergrond/tegel-laag.  
* [:backend:`4321`] Formulieren kunnen nu een inzendingslimiet hebben. Het SDK toont passende meldingen wanneer deze 
  limiet is bereikt.  
* [:backend:`4895`] Metadata toegevoegd aan uitgaande bevestigings- en mede-ondertekeningsverzoek-e-mails.  
* [:backend:`4789`, :backend:`4788`, :backend:`4787`] Toegevoegd: ``django-setup-configuration`` om Open Formulieren 
  programmatisch te configureren met verbindingsdetails voor Objecten en ZGW API's. U kunt een configuratiebestand 
  laden via het ``setup_configuration`` management-commando. Aanvullende informatie/instructies zijn te vinden 
  in :ref:`installation_configuration_cli`.  
* [:backend:`4798`] Consistentie toegevoegd aan de bevestigingsbox en verbeterde UX van andere modals.  
* [:backend:`4320`] Verbeteringen aan de mede-ondertekeningsflow en de bijbehorende teksten toegevoegd, evenals meer 
  flexibiliteit:  

    - Specifieke sjablonen voor medeondertekening kunnen nu worden gebruikt voor de inhoud van de bevestigingsschermen, 
      inclusief de optie om een 'nu medeondertekenen'-knop toe te voegen.  
    - Specifieke sjablonen voor medeondertekening kunnen nu worden gebruikt voor de onderwerpregel en inhoud van de 
      bevestigingse-mail.  
    - Wanneer links worden gebruikt in de e-mail met mede-ondertekeningsverzoeken, kan de medeondertekenaar nu direct 
      doorklikken zonder een code in te voeren om de inzending te bekijken.  
    - De standaard sjablonen zijn bijgewerkt met betere teksten/instructies.  
    - Vertalingen van verbeterde teksten zijn bijgewerkt.  
* [:backend:`4815`] De minimale verwijderlimiet voor inzendingen is nu 0 dagen, zodat inzendingen op dezelfde dag 
  verwijderd kunnen worden.  
* [:backend:`4717`] Verbeterde toegankelijkheid voor site-logo, foutboodschap-element en PDF-documenten.  
* [:backend:`4719`] Toegankelijkheid verbeterd in postcodevelden.  
* [:backend:`4707`] Json-Logic-widgets kunnen nu worden aangepast qua grootte.  
* [:backend:`4720`] Toegankelijkheid verbeterd voor de skiplink en het PDF-rapport.  
* [:backend:`4764`] Mogelijkheid toegevoegd om de prijsberekening van inzendingen als variabele in te stellen.  
* [:backend:`4716`] Vertalingen toegevoegd voor formulier-velden en bijbehorende verbeteringen in foutmeldingen.  
* [:backend:`4524`, :backend:`4675`] Selecteren van een formulier-variabele is nu gebruiksvriendelijker. Variabelen 
  worden logisch gegroepeerd en een zoekveld is toegevoegd.  
* [:backend:`4709`] Verbeterde foutfeedback bij onverwachte fouten tijdens het opslaan van een formulier in de 
  formulier-editor.  

**Bugfixes**  

* [:backend:`4978`] Opgelost: onbedoelde HTML-escaping in samenvatting PDF/bevestigingse-mail en markering van een 
  variabele als een geometrische variabele.  
* Hulpteksten in Objecten API Prefill opgelost.  
* [:backend:`4579`] Fout opgelost waarbij verkeerde stappen werden geblokkeerd wanneer logica de optie "trigger from 
  step" gebruikte.  
* [:backend:`4900`] Fout opgelost met opnieuw koppelen van inzendingswaardevariabelen voor herbruikbare 
  formulier-definities.  
* [:backend:`4795`] Niet altijd mogelijk om ``.msg``- en ``.zip``-bestanden te uploaden, opgelost.  
* [:backend:`4825`] Prefill-fouten worden nu alleen gelogd voor de relevante authenticatiestroom toegepast in een 
  formulier.  
* [:backend:`4863`] Crash opgelost wanneer organisatie-login wordt gebruikt voor een formulier.  
* [:backend:`4955`] Verkeerde volgorde van lat/lng-coördinaten in Objecten API en ZGW API registratie opgelost.  
* [:backend:`4821`] Fout opgelost waarbij e-maildigest BRK/addressNL-configuratieproblemen verkeerd rapporteerde.  
* [:backend:`4949`] Close-knop van modal in donkere modus opgelost.  
* [:backend:`4886`] Probleem opgelost waarbij bepaalde varianten van CSV-bestanden niet valideerden op Windows.  
* [:backend:`4832`] Bepaalde objecttype-eigenschappen die niet beschikbaar waren in de registratievariabelen-mapping 
  opgelost.  
* [:backend:`4853`, :backend:`4899`] Fout opgelost waarbij lege optionele configuratievelden niet valideerden in 
  meerdere registratie-backends.  
* [:backend:`4884`] Zorgen dat geen formulier-variabelen worden aangemaakt voor soft-required foutencomponenten.  
* [:backend:`4874`] Opgelost: ontbrekende scripts in Dockerfile.  
* [:backend:`3901`] Status van medeondertekening hield geen rekening met logica/dynamisch gedrag van de 
  mede-ondertekeningscomponent.  
* [:backend:`4824`] Formulier-variabelen worden nu correct gesynchroniseerd met de staat van FormDefinition na het 
  opslaan.  
* Fout in Django-admin formulier-veldopmaak na Django v4.2 opgelost.  

**Projectonderhoud**  

* Documentatie bijgewerkt met betrekking tot frontend-toolchains en zoekstrategieën van Formio.  
* [:backend:`4907`] Installatiedocumentatie voor ontwikkelaars verbeterd.  
* Storybook-setup verbeterd om dichter bij daadwerkelijk gebruik in Django-admin te staan.  
* [:backend:`4920`] Migrations opgeschoond en samengevoegd waar mogelijk.  
* Open Formulieren versie-upgradepadcontroles ontdubbeld.  
* Vervallen domeinen voor VCR-tests gedocumenteerd.  
* Stabiliteit in testsuite verhoogd.  
* [:backend:`3457`] Uitgebreide typecontrole toegepast op de meeste delen van de betalingsapp.  
* Migratietests verwijderd die afhankelijk waren van echte modellen.  
* Waarschuwingen in DMN-componenten aangepakt.  
* Ongebruikte ``uiSchema``-eigenschap uit registratievelden verwijderd.  
* Overbodige `.admin-fieldset`-styling verwijderd.  
* Aangepaste helptekst-styling verwijderd en standaard Django-styling toegepast.  
* ``summary``-tag implementatie vervangen door ``confirmation_summary``.  
* Verhalen in de variabeleneditor bijgewerkt/geherstructureerd.  
* [:backend:`4398`] ``TargetPathSelect``-component herzien.  
* [:backend:`4849`] Template voor releasevoorbereiding bijgewerkt met ontbrekende VCR-paden.  
* API-eindpunten bijgewerkt met correct taalgebruik (NL -> EN).  
* [:backend:`4431`] Backwards compatibility voor addressNL-mapping verbeterd en Objecten API v2-handler herzien.  
* Recursieproblemen opgelost in componentzoekstrategieën.  
* Duplicaatcode vervangen voor betalings-/registratieplugin-configuratieopties door generieke componenten.  
* React-configuratieformulier specifiek gemaakt voor MS Graph-registratieopties.  
* Demo-pluginsconfiguratie geüpdatet om modaal te gebruiken.  
* CI-workflow opgeschoond.  
* Versie 2.6.x verwijderd uit ondersteunde versies in Docker Hub-beschrijving.  
* Versie 2.8.x toegevoegd aan Docker Hub-beschrijving.  
* [:backend:`4721`] Screenshots in documentatie voor Prefill en Objecten API-handleiding bijgewerkt.  
* Versie 2.5 verplaatst naar niet-ondersteunde versies in ontwikkelaarsdocumentatie en EOL-status van 2.5.x 
  gedocumenteerd.  
* Frontend-afhankelijkheden bijgewerkt:  

    - Upgraded naar MSW 2.x.  
    - RJSF verwijderd.  
    - Storybook bijgewerkt naar 8.3.5.  

* Backend-afhankelijkheden bijgewerkt:  

    - Jinja2 geüpgraded naar 3.1.5.  
    - Django geüpgraded naar 4.2.17 patch-versie.  
    - Tornado-versie bijgewerkt.  
    - lxml-html-cleaner geüpgraded.  
    - Waitress geüpgraded.  
    - django-silk-versie bijgewerkt voor compatibiliteit met Python 3.12.  
    - Trivy-action bijgewerkt naar 0.24.0.  
