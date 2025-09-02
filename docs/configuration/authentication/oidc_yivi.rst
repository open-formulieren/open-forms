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

Yivi-attribuutgroepen
---------------------

Bij elke authenticatiemethode kunnen aanvullende attributen worden uitgevraagd. Hiermee
kunnen, naast identificatiegegevens, ook extra persoons- of bedrijfsgegevens worden
verkregen.

In Open Formulieren kunnen deze aanvullende attributen worden gedefinieerd als
:ref:`Yivi-attribuutgroepen <configuration_oidc_yivi_attribute_groups>`. Deze
attribuutgroepen kunnen vervolgens worden geconfigureerd in formulieren die gebruikmaken
van de ``Yivi via OpenID Connect`` authenticatie-plugin.

Elke attribuutgroep is per stuk optioneel; de gebruiker bepaalt zelf welke groepen wel
en niet te voorzien van informatie.

In Open Formulieren kunnen Yivi-attribuutgroepen geëxporteerd en geïmporteerd worden.
Zo kunt u eenvoudig attribuutgroepen delen met anderen of overzetten van een test- naar
productie-omgeving.

.. important:: Alle verzoeken aan Yivi vereisen het gebruik van Yivi-attributen. Ook voor
   de BSN, KVK en betrouwbaarheidsniveau claims, moeten Yivi-attributen gebruikt worden.
   Raadpleeg de `Yivi Attribute Index`_ voor een volledig overzicht van alle beschikbare
   attributen.

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

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC provider** > **oidc-yivi-provider**.

Hier kan je de endpoints van de OIDC provider inrichten. Deze kunnen automatisch
bepaald worden aan de hand van het discovery endpoint
(``https://login.gemeente.nl/auth/realms/{realm}/.well-known/openid-configuration``).

#. Vul bij **Discovery endpoint** het pad naar het juiste authenticatie realm endpoint
   van de OpenID Connect provider in (met een ``/`` op het einde),
   bijvoorbeeld ``https://login.gemeente.nl/auth/realms/{realm}/``.
#. Laat de overige endpoints leeg - deze worden automatisch aangevuld.

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC clients** > **oidc-yivi**.

Begin met de algemene instellingen.
Stel de algemene instellingen in:

#. Vink *Ingeschakeld* aan om OIDC in te schakelen.
#. Selecteer de provider die je net heb geconfigureerd in de **OIDC Provider** dropdown.
#. Vul bij **OpenID Connect client ID** het Client ID in, bijvoorbeeld
   ``a7d14516-8b20-418f-b34e-25f53c930948``.
#. Vul bij **OpenID Connect secret** het Client secret in, bijvoobeeld
   ``97d663a9-3624-4930-90c7-2b90635bd990``.
#. Laat bij **OpenID Connect scopes** de standaardwaarden staan, of stel deze in volgens
   de instructies van je OpenID Connect provider.
#. Vul bij **OpenID sign algorithm** ``RS256`` in.
#. Laat **Sign key** leeg.

Stel dan de claims in:

Beginnend bij de claims gebruikt voor BSN-authenticatie.

#. Voer bij **Identity settings** > **BSN claim path** het pad van de claim in die het
   BSN bevat, bijvoorbeeld ``pbdf.gemeente.personalData.bsn``.
#. Voer bij **LoA settings** > **BSN loa claim path** het pad van de claim in als die
   bekend is, bijvoorbeeld ``pbdf.gemeente.personalData.digidlevel``. Indien niet,
   kies dan bij **LoA settings** > **BSN Default loa** de waarde die het meest
   van toepassing is. Dit wordt enkel gebruikt om vast te leggen met welk
   betrouwbaarheidsniveau iemand ingelogd is.
#. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus
   toevoegen, bijvoorbeeld:

   * klik op "Add item"
   * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``10`` op in het
     tekstveld
   * Selecteer "DigiD Basis" in de **To** dropdown
   * Herhaal voor andere waarden en niveaus

Vervolgens richt je de claims voor KVK-authenticatie in.

#. Vul bij **Identity settings** > **KvK claim path** de claim in die het KVK-nummer
   bevat, bijvoorbeeld ``pbdf.signicat.kvkTradeRegister.kvkNumber``.
#. Voer bij **LoA settings** > **KvK loa claim path** het pad van de claim in als die
   bekend is. Indien niet, kies dan bij **LoA settings** > **KvK Default loa** de waarde
   die het meest van toepassing is. Dit wordt enkel gebruikt om vast te leggen met welk
   betrouwbaarheidsniveau iemand ingelogd is.
#. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus
   toevoegen, bijvoorbeeld:

   * klik op "Add item"
   * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``00`` op in het
     tekstveld
   * Selecteer "Non existent" in de **To** dropdown
   * Herhaal voor andere waarden en niveaus

Daarna richt je de claim voor authenticatie met pseudoniem in.

* De standaard waarde voor **Identity settings** > **Pseudo claim path** zal een Yivi-applicatie unieke waarde
  opleveren. Indien gewenst kan je dit veranderen naar een andere identificatie waarde,
  zoals een e-mailadres.

Vervolgens kan je de **Configuratie** > **Yivi Attribuutgroepen** instellen. Deze zijn niet noodzakelijk om de
Yivi-plugin te kunnen gebruiken, maar bieden wel meer mogelijkheden voor gebruikers en
formulierbouwers.

* Indien gewenst, kan je instellen welke attributen op formulierniveau geconfigureerd
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
  * De waarde voor het **UUID** wordt automatisch bepaald. Dit is een sleutelwaarde die
    in Open Formulieren wordt gebruikt als verwijzing naar deze Attribuutgroep.
  * Voor een volgende attributengroep, klik op "Nog een Attribuutgroep toevoegen" en
    herhaal de vorige stappen.

Klik tot slot linksonder op **Opslaan**.

Je kan nu een formulier aanmaken met de ``Yivi via OpenID Connect``
authenticatie-plugin, zie :ref:`manual_forms_basics`.

.. _configuration_oidc_yivi_attribute_groups:

Configureren van Yivi-attribuutgroepen in Open Formulieren
==========================================================

Navigeer in de admin naar **Configuratie** > **Yivi-attribuutgroepen** en klik op
**Yivi-attribuutgroep toevoegen**.

1. Vul bij **groepsnaam** een duidelijke en herkenbare naam in voor de groep.
   (Deze naam wordt alleen gebruikt in de formulierconfiguratie ter identificatie van de
   groep en heeft verder geen functionele waarde.)

2. Vul bij **groepsbeschrijving** een korte beschrijving van de groep.
   (Deze beschrijving wordt alleen gebruikt in de formulierconfiguratie ter
   verduidelijking van de groep en heeft verder geen functionele waarde.)

3. Vul bij **Attributen** de Yivi-attributen toe die tijdens het inloggen bevraagd moeten
   worden. De beschikbare attributen zijn te vinden in de `Yivi Attribute Index`_.
   Als de gebruiker deze attributen beschikbaar stelt, kunnen ze gebruikt worden voor
   :ref:`voorinvullen (prefill) <example_prefill>`.
   Klik op **Add item** om meerdere attributen toe te voegen.

Klik vervolgens linksonder op **Opslaan** om de configuratie op te slaan.

De aangemaakte attributengroep is nu beschikbaar voor gebruik in formulieren die
gebruikmaken van de ``Yivi via OpenID Connect`` authenticatie-plugin.

.. _Yivi Attribute Index: https://portal.yivi.app/attribute-index
