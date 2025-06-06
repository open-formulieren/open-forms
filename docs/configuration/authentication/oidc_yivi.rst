.. _configuration_authentication_oidc_yivi:

=====================================
OpenID Connect voor inloggen met Yivi
=====================================

Open Formulieren ondersteunt Yivi login voor burgers en ondernemers via het OpenID Connect protocol (OIDC).

Burgers en ondernemers kunnen op die manier inloggen op Open Formulieren met hun DigiD of eHerkenning account
of anoniem. In deze flow:

1. Klikt een gebruiker in een formulier op de knop *Inloggen met Yivi*
2. De gebruiker wordt via de omgeving van de OpenID Connect provider (bijv. Keycloak)
   naar Yivi geleid, waar de gebruiker kan inloggen middels een authenticatie opties naar
   keuze.

     In bepaalde gevallen kan om aanvullende gegevens van de gebruiker gevraagd worden.
     De gebruiker kan zelf bepalen deze gegevens te verstrekken.

3. Yivi stuurt de gebruiker terug naar de OIDC omgeving, die op zijn beurt de gebruiker
   weer terugstuurt naar Open Formulieren.
4. De gebruiker is ingelogd en kan verder met het invullen van het formulier.

Om gebruik te maken van Yivi dient de gebruiker te beschikken over een mobiele telefoon,
met daarop de Yivi authenticator applicatie.

.. _configuration_oidc_yivi_claim_requirements:

Claim-eisen
===========

De OpenID Connect provider moet na een succesvolle login met Yivi een aantal claims
aanbieden aan Open Formulieren, aan de hand van de gekozen authenticatie optie. De
precieze namen van deze claims kunnen ingesteld worden in Open Formulieren.

Voor authenticatie met BSN
--------------------------

Wanneer een gebruiker kiest voor authenticatie met BSN, worden deze claims verwacht na de
login:

``BSN``
    Het BSN van de ingelogde gebruiker. Altijd verplicht.

``betrouwbaarheidsniveau``
    Het betrouwbaarheidsniveau gebruikt tijdens het inloggen. Dit wordt vastgelegd en
    meegestuurd tijdens het registeren van formulierinzendingen. Als de provider dit
    niet kan aanleveren, dan kan je een standaardwaarde instellen in Open Formulieren.

    Beheerders kunnen waardenvertalingen inrichten indien de provider de waarden
    niet aanlevert zoals gedocumenteerd in de koppelvlakstandaard van Logius.

Voor authenticatie met KVK
--------------------------

Wanneer een gebruiker kiest voor authenticatie met KVK, worden deze claims verwacht na de
login:

``name qualifier``
    De waarde geeft aan of het bedrijf met RSIN of KVK-nummer inlogt. Indien niet
    gegeven, dan gaat Open Formulieren uit van een KVK-nummer.

``legalSubject``
    Het KVK-nummer of RSIN van het bedrijf. Altijd verplicht.

``actingSubject``
    De (versleutelde) identificatie van de medewerker die inlogt namens het bedrijf.

    Verplicht indien ``DIGID_EHERKENNING_OIDC_STRICT``
    (:ref:`installation_environment_config`) op ``True`` staat.

``vestigingsNummer``
    Identificatie van de/een vestiging van het bedrijf. Nooit verplicht. Indien niet
    opgegeven, dan is de aanname dat het de hoofdvestiging betreft.

``betrouwbaarheidsniveau``
    Het betrouwbaarheidsniveau gebruikt tijdens het inloggen. Dit wordt vastgelegd en
    meegestuurd tijdens het registeren van formulierinzendingen. Als de provider dit
    niet kan aanleveren, dan kan je een standaardwaarde instellen in Open Formulieren.

    Beheerders kunnen waardenvertalingen inrichten indien de provider de waarden
    niet aanlevert zoals gedocumenteerd in de koppelvlakstandaard van Logius.

.. warning:: Open Formulieren ondersteunt op dit moment enkel KVK-nummers en niet RSIN.

Voor anonieme authenticatie
---------------------------

Wanneer een gebruiker anonieme authenticatie, wordt deze claim verwacht na de login:

``pseudo identifier claim``
    De (versleutelde) identificatie van de gebruiker die inlogt.

Voor aanvullende scopes
-----------------------

Voor iedere authenticatie methode kunnen aanvullende scopes gevraagd worden. Een *scope*
(toegangsbereik) bepaalt welke gegevens een applicatie mag opvragen. Hiermee kunnen,
naast de identificatie gegevens, ook aanvullende persoons- of bedrijfsgegevens opgevraagd
worden.

Om zowel flexibiliteit als gemak te bieden, kan je in de Yivi configuratie defineren welke
scopes voor Yivi gebruikt kunnen worden, om deze vervolgens per formulier in te stellen.
Hiermee worden de scopes alleen toegepast op de formulieren waarvoor deze benodigd zijn.

``scope``
    Naam van de scope die bij Yivi uitgevraagd kan worden.

``claims``
    De claims die beschikbaar worden door middel van het gebruik van de scope. Wanneer de
    gebruiker deze gegevens aanbiedt, kunnen deze gebruikt worden bij het
    :ref:`voorinvullen (prefill) <example_prefill>`.

.. _configuration_oidc_yivi_appgroup:

Configureren van OIDC-provider
==============================

Contacteer de IAM beheerders in je organisatie om een *Client* aan te maken in de
omgeving van de OpenID Connect provider.

**Redirect URI (vanaf Open Formulieren 2.7.0)**

.. versionchanged:: 3.0

    Open Forms no longer uses the legacy endpoints by default.

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/auth/oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein.

**Redirect URI (legacy)**

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/yivi-oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein.

**Gegevens**

Aan het eind van dit proces moet je de volgende gegevens hebben:

* Server adres, bijvoorbeeld ``login.gemeente.nl``
* Client ID, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``
* Client secret, bijvoorbeeld ``97d663a9-3624-4930-90c7-2b90635bd990``

Configureren van OIDC in Open Formulieren
=========================================

Zorg dat je de volgende :ref:`gegevens <configuration_oidc_yivi_appgroup>` hebt:

* Server adres
* Client ID
* Client secret

Navigeer vervolgens in de admin naar **Configuratie** > **Yivi (OIDC)**.

Stel de algemene instellingen in:

1. Vink *Ingeschakeld* aan om OIDC in te schakelen.
2. Vul bij **OpenID Connect client ID** het Client ID in, bijvoorbeeld
   ``a7d14516-8b20-418f-b34e-25f53c930948``.
3. Vul bij **OpenID Connect secret** het Client secret in, bijvoobeeld
   ``97d663a9-3624-4930-90c7-2b90635bd990``.
4. Laat bij **OpenID Connect scopes** de standaardwaarden staan, of stel deze in volgens
   de instructies van je OpenID Connect provider.
5. Vul bij **OpenID sign algorithm** ``RS256`` in.
6. Laat **Sign key** leeg.

Stel dan de claims in:

Beginnend bij de claims gebruikt voor BSN authenticatie.

7. Laat bij **BSN-scope** de standaardwaarde staan, tenzij de scope voor BSN
   authenticatie in de OpenID Connect provider anders is dan ``bsn``.
8. Laat bij **BSN-claim** de standaardwaarde staan, tenzij de naam van het BSN veld
   in de OIDC claims anders is dan ``bsn``.
9. Voer bij **betrouwbaarheidsniveau-claim** de naam van de claim in (bijvoorbeeld
   ``authsp_level``) als die bekend is. Indien niet, kies dan bij
   **Standaardbetrouwbaarheidsniveau** de waarde die meest van toepassing is. Dit wordt
   enkel gebruikt om vast te leggen met welk betrouwbaarheidsniveau iemand ingelogd is.
10. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus
    toevoegen, bijvoorbeeld:

    * klik op "Add item"
    * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``10`` op in het
      tekstveld
    * Selecteer "DigiD Basis" in de **To** dropdown
    * Herhaal voor andere waarden en niveaus

Vervolgens richt je de claims voor KVK authenticatie in.

11. Laat bij **KVK-scope** de standaardwaarde staan, tenzij de scope voor KVK
    authenticatie in de OpenID Connect provider anders is dan ``kvk``.
12. Vul bij **Soort identificatie-claim** de claim in die aangeeft of het een KVK-nummer
    of RSIN betreft (merk op: op dit moment ondersteunen we enkel KVK). Indien onbekend,
    dan kan je de standaardwaarde laten staan.
13. Vul bij **Bedrijfsidenticatie-claim** de claim in die het KVK-nummer (of RSIN,
    toekomst) bevat, bijvoorbeeld ``kvk``.
14. Vul de claim in die het (eventuele) vestigingsnummer bevat bij
    **Vestigingsnummer-claim**. Indien onbekend, laat dan de standaardwaarde staan.
15. Vul bij **Identificatie handelende persoon-claim** de claim in die de identificatie
    bevat van de medewerker die namens het bedrijf inlogt.
16. Voer bij **betrouwbaarheidsniveau-claim** de naam van de claim in (bijvoorbeeld
    ``authsp_level``) als die bekend is. Indien niet, kies dan bij
    **Standaardbetrouwbaarheidsniveau** de waarde die meest van toepassing is. Dit wordt
    enkel gebruikt om vast te leggen met welk betrouwbaarheidsniveau iemand ingelogd is.
17. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus
    toevoegen, bijvoorbeeld:

    * klik op "Add item"
    * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``00`` op in het
      tekstveld
    * Selecteer "Non existent" in de **To** dropdown
    * Herhaal voor andere waarden en niveaus

Daarna richt je de claim voor anonieme authenticatie in.

18. Laat bij **Pseudoniem-claim** de standaardwaarde staan, tenzij de naam van het
    pseudoniem veld in de OIDC claims anders is dan ``sub``.

Na de verschillende authenticatie claims richt je de endpoints van de OIDC provider in,
deze kunnen automatisch bepaald worden aan de hand van het discovery endpoint
(``https://login.gemeente.nl/auth/realms/{realm}/.well-known/openid-configuration``).

19. Vul bij **Discovery endpoint** het pad naar het juiste authenticatie realm endpoint
    van de OpenID Connect provider in (met een ``/`` op het einde),
    bijvoorbeeld ``https://login.gemeente.nl/auth/realms/{realm}/``.
20. Laat de overige endpoints leeg - deze worden automatisch aangevuld.

Vervolgens kan je de beschikbare scopes nog instellen. Deze zijn niet strikt nodig om de
Yivi plugin te kunnen gebruiken, deze bieden wel meer mogelijkheden voor gebruikers en
formulierbouwers.

21. Indien gewenst, kan je instellen welke scopes op formulier niveau geconfigureerd
    kunnen worden, bijvoorbeeld:

    * Type in het **Scope** tekstveld de naam van de scope in
    * In **Scope beschrijving** kan je de scope een begrijpelijke naam geven, hiermee
      kunnen formulierbouwers gemakkelijk herkennen waar de scope voor dient en welke
      informatie ermee beschikbaar wordt.
    * Type in het **Claims resulterend uit scope** tekstveld de naam van de claim die met
      deze scope beschikbaar wordt. In het geval dat er meerdere claims uit de scope
      voortkomen, klik op "Add item" en herhaal totdat je alle claims hebt gedefinieerd.
    * Voor een volgende scope, klik op "Add another Available scope" en herhaal de vorige
      stappen

Klik tot slot linksonder op **Opslaan**.

Je kan nu een formulier aanmaken met de ``Yivi via OpenID Connect``
authenticatie-plugin, zie :ref:`manual_forms_basics`.
