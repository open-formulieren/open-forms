.. _configuration_authentication_oidc_yivi:

=====================================
OpenID Connect voor inloggen met Yivi
=====================================

Open Formulieren ondersteunt `Yivi login <https://yivi.app/>`_ voor burgers en
ondernemers via het OpenID Connect protocol (OIDC).

Burgers en ondernemers kunnen op die manier inloggen op Open Formulieren met hun DigiD-
of eHerkenning-account of anoniem. In deze flow:

1. Klikt een gebruiker in een formulier op de knop *Inloggen met Yivi*
2. De gebruiker wordt via de omgeving van de OpenID Connect provider (bijv. Keycloak)
   naar Yivi geleid, waar de gebruiker kan inloggen middels authenticatie-opties naar
   keuze.

     Per formulier kunnen aanvullende gegevens van de gebruiker gevraagd worden.
     De gebruiker kan zelf bepalen deze gegevens te verstrekken.

3. Yivi stuurt de gebruiker terug naar de OIDC-omgeving, die op zijn beurt de gebruiker
   weer terugstuurt naar Open Formulieren.
4. De gebruiker is ingelogd en kan verder met het invullen van het formulier.

Om gebruik te maken van Yivi dient de gebruiker te beschikken over een mobiele telefoon,
met daarop de Yivi authenticator-applicatie.

.. _configuration_oidc_yivi_claim_requirements:

Claim-eisen
===========

De OpenID Connect provider moet na een succesvolle login met Yivi een aantal claims
aanbieden aan Open Formulieren, afhankelijk van de gekozen authenticatie-optie. De
precieze namen van deze claims kunnen ingesteld worden in Open Formulieren.

Voor authenticatie met BSN
--------------------------

Wanneer een gebruiker kiest voor authenticatie met BSN, worden deze claims verwacht na de
login:

``BSN``
    Het BSN van de ingelogde gebruiker. Altijd verplicht.

``betrouwbaarheidsniveau``
    Het betrouwbaarheidsniveau gebruikt tijdens het inloggen. Dit wordt vastgelegd en
    meegestuurd tijdens het registeren van formulierinzendingen. Als er geen claim is
    ingevuld voor het betrouwbaarheidsniveau, dan wordt de standaardwaarde gebruik
    (instelbaar in Open Formulieren).

    Beheerders kunnen waardenvertalingen inrichten indien de provider de waarden
    niet aanlevert zoals gedocumenteerd in de koppelvlakstandaard van Logius.

Voor authenticatie met KVK
--------------------------

Wanneer een gebruiker kiest voor authenticatie met KVK, worden deze claims verwacht na de
login:

``KVK``
    Het KVK-nummer van het bedrijf. Altijd verplicht.

``betrouwbaarheidsniveau``
    Het betrouwbaarheidsniveau gebruikt tijdens het inloggen. Dit wordt vastgelegd en
    meegestuurd tijdens het registeren van formulierinzendingen. Als er geen claim is
    ingevuld voor het betrouwbaarheidsniveau, dan wordt de standaardwaarde gebruik
    (instelbaar in Open Formulieren).

    Beheerders kunnen waardenvertalingen inrichten indien de provider de waarden
    niet aanlevert zoals gedocumenteerd in de koppelvlakstandaard van Logius.

Voor authenticatie met pseudoniem
---------------------------------

Wanneer een gebruiker kiest voor authenticatie met pseudoniem, wordt deze claim verwacht
na de login:

``pseudo identifier claim``
    De identificatie van de gebruiker die inlogt.

Voor aanvullende attributen
---------------------------

Voor iedere authenticatiemethode kunnen aanvullende attributengroepen gevraagd worden.
Hiermee kunnen, naast de identificatiegegevens, ook aanvullende persoons- of
bedrijfsgegevens opgevraagd worden.

Om zowel flexibiliteit als gemak te bieden, kan je in de Yivi-configuratie definiëren
welke attributen voor Yivi gebruikt kunnen worden. Deze kunnen vervolgens per formulier
ingesteld worden. Hiermee worden de attributen alleen toegepast op de formulieren
waarbij deze van toepassing zijn.

``group name``
    Naam van de attributengroep. Dit is een herkenbare naam voor de formulierbouwers en
    heeft verder geen betekenis.

``group description``
    Beschrijving van de attributengroep. Dit kan gebruikt worden om aanvullende
    informatie te geven over de attributengroep, zoals welke gegevens hiermee opgevraagd
    kunnen worden. Net als de naam, wordt dit gebruikt als extra context voor
    formulierbouwers en heeft verder geen betekenis.

``attributes``
    De attributen die aan de gebruiker gevraagd worden. Wanneer de gebruiker deze
    gegevens aanbiedt, worden deze beschikbaar bij het
    :ref:`voorinvullen (prefill) <example_prefill>`.
    De attribuutgroepen zijn per stuk optioneel; de gebruiker kan zelf bepalen welke
    attribuutgroepen wel en niet aan te leveren.

.. _configuration_oidc_yivi_appgroup:

Configureren van OIDC-provider
==============================

Contacteer de IAM beheerders in je organisatie om een *Client* aan te
maken in de omgeving van de OpenID Connect provider.

**Redirect URI**

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/auth/oidc/callback/`` in,
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

Begin met de algemene instellingen.
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

Beginnend bij de claims gebruikt voor BSN-authenticatie.

7. Voer bij **BSN-claim** de naam van de claim in die het BSN bevat.
8. Voer bij **betrouwbaarheidsniveau-claim** de naam van de claim in als die bekend is.
   Indien niet, kies dan bij **Standaardbetrouwbaarheidsniveau** de waarde die het meest
   van toepassing is. Dit wordt enkel gebruikt om vast te leggen met welk
   betrouwbaarheidsniveau iemand ingelogd is.
9. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus
   toevoegen, bijvoorbeeld:

   * klik op "Add item"
   * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``10`` op in het
     tekstveld
   * Selecteer "DigiD Basis" in de **To** dropdown
   * Herhaal voor andere waarden en niveaus

Vervolgens richt je de claims voor KVK-authenticatie in.

10. Vul bij **kvk-claim** de claim in die het KVK-nummer bevat.
11. Voer bij **betrouwbaarheidsniveau-claim** de naam van de claim in als die bekend is.
    Indien niet, kies dan bij **Standaardbetrouwbaarheidsniveau** de waarde die het meest
    van toepassing is. Dit wordt enkel gebruikt om vast te leggen met welk
    betrouwbaarheidsniveau iemand ingelogd is.
12. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus
    toevoegen, bijvoorbeeld:

    * klik op "Add item"
    * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``00`` op in het
      tekstveld
    * Selecteer "Non existent" in de **To** dropdown
    * Herhaal voor andere waarden en niveaus

Daarna richt je de claim voor authenticatie met pseudoniem in.

13. De standaard waarde voor **Pseudoniem-claim** zal een Yivi-applicatie unieke waarde
    opleveren. Indien gewenst kan je dit veranderen naar een andere identificatie waarde,
    zoals een e-mailadres.

Na de verschillende authenticatie claims richt je de endpoints van de OIDC-provider in,
deze kunnen automatisch bepaald worden aan de hand van het discovery endpoint
(``https://login.gemeente.nl/auth/realms/{realm}/.well-known/openid-configuration``).

14. Vul bij **Discovery endpoint** het pad naar het juiste authenticatie realm endpoint
    van de OpenID Connect provider in (met een ``/`` op het einde),
    bijvoorbeeld ``https://login.gemeente.nl/auth/realms/{realm}/``.
15. Laat de overige endpoints leeg - deze worden automatisch aangevuld.

Vervolgens kan je de **Attribuutgroepen** instellen. Deze zijn niet noodzakelijk om de
Yivi-plugin te kunnen gebruiken, maar bieden wel meer mogelijkheden voor gebruikers en
formulierbouwers.

16. Indien gewenst, kan je instellen welke attributen op formulierniveau geconfigureerd
    kunnen worden, bijvoorbeeld:

    * Typ in het **Groepnaam** tekstveld de naam van de groep in. Deze waarde wordt
      enkel gebruikt om de attributenverzameling herkenbaar te maken in de
      formulier-editor.
    * In **Groepsbeschrijving** kan je de groep een begrijpelijke omschrijving geven,
      hiermee kunnen formulierbouwers gemakkelijk herkennen waar de groep attributen voor
      dient en welke gegevens ermee verzameld worden.
    * Typ in het **Attributen**-tekstveld het attribuut dat voor deze groep gebruikt zal
      worden. Om meerdere attributen in dezelfde groep te plaatsen, klik op "Add item"
      en herhaal totdat je alle gewenste attributen hebt gedefinieerd.
    * Voor een volgende attributengroep, klik op "Nog een Attribuutgroep toevoegen" en
      herhaal de vorige stappen.

Klik tot slot linksonder op **Opslaan**.

Je kan nu een formulier aanmaken met de ``Yivi via OpenID Connect``
authenticatie-plugin, zie :ref:`manual_forms_basics`.
