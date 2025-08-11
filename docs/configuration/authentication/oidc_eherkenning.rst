.. _configuration_authentication_oidc_eherkenning:

============================================
OpenID Connect voor inloggen met eHerkenning
============================================

Open Formulieren ondersteunt eHerkenning login voor ondernemers via het OpenID Connect protocol (OIDC).

Ondernemers kunnen op die manier inloggen op Open Formulieren met hun eHerkenning account. In deze
flow:

1. Klikt een gebruiker in een formulier op de knop *Inloggen met eHerkenning*
2. De gebruiker wordt via de omgeving van de OpenID Connect provider (bijv. Keycloak) naar eHerkenning geleid,
   waar de gebruiker kan inloggen
3. eHerkenning stuurt de gebruiker terug naar de OIDC omgeving, die op zijn beurt de gebruiker weer terugstuurt naar Open Formulieren
4. De gebruiker is ingelogd en kan verder met het invullen van het formulier

.. _configuration_oidc_eherkenning_claim_requirements:

Claim-eisen
===========

De OpenID Connect provider moet na een succesvolle login met DigiD een aantal claims
aanbieden aan Open Formulieren. De precieze namen van deze claims kunnen ingesteld
worden in Open Formulieren.

``name qualifier``
    De waarde geeft aan of het bedrijf met RSIN of KVK-nummer inlogt. Indien niet
    gegeven, dan gaat Open Formulieren uit van een KVK-nummer.

``legalSubject``
    Het KVK-nummer of RSIN van het bedrijf. Altijd verplicht.

``actingSubject``
    De (versleutelde) identificatie van de medewerker die inlogt namens het bedrijf.

    Verplicht indien ``DIGID_EHERKENNING_OIDC_STRICT`` (:ref:`installation_environment_config`) op ``True`` staat.

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

.. _configuration_oidc_eherkenning_appgroup:

Configureren van OIDC-provider
==============================

Contacteer de IAM beheerders in je organisatie om een *Client* aan te
maken in de omgeving van de OpenID Connect provider.

**Redirect URI (vanaf Open Formulieren 2.7.0)**

.. versionchanged:: 3.0

    Open Forms no longer uses the legacy endpoints by default.

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/auth/oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein.

**Redirect URI (legacy)**

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/eherkenning-oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein.

**Gegevens**

Aan het eind van dit proces moet je de volgende gegevens hebben:

* Server adres, bijvoorbeeld ``login.gemeente.nl``
* Client ID, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``
* Client secret, bijvoorbeeld ``97d663a9-3624-4930-90c7-2b90635bd990``

Configureren van OIDC in Open Formulieren
=========================================

Zorg dat je de volgende :ref:`gegevens <configuration_oidc_eherkenning_appgroup>` hebt:

* Server adres
* Client ID
* Client secret

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC Providers** > **eherkenning-oidc-provider**.

Hier kan je de endpoints van de OIDC provider inrichten. Deze kunnen automatisch
bepaald worden aan de hand van het discovery endpoint
(``https://login.gemeente.nl/auth/realms/{realm}/.well-known/openid-configuration``).

#. Vul bij **Discovery endpoint** het pad naar het juiste authenticatie realm endpoint
    van de OpenID Connect provider in (met een ``/`` op het einde),
    bijvoorbeeld ``https://login.gemeente.nl/auth/realms/{realm}/``.
#. Laat de overige endpoints leeg - deze worden automatisch aangevuld.

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC Clients** > **eherkenning-oidc**.

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

Stel dan de eHerkenning specifieke instellingen in de **opties** veld:

#. Vul bij **Identity settings** > **Soort identificatie-claim-pad** de claim in die aangeeft of het een KVK-nummer
   of RSIN betreft (merk op: op dit moment ondersteunen we enkel KVK). Indien onbekend,
   dan kan je de standaardwaarde laten staan.
#. Vul bij **Identity settings** > **Bedrijfsidenticatie-claim** de claim in die het KVK-nummer (of RSIN,
   toekomst) bevat, bijvoorbeeld ``kvk``.
#. Vul de claim in die het (eventuele) vestigingsnummer bevat bij
   **Identity settings** > **Vestigingsnummer-claim**. Indien onbekend, laat dan de standaardwaarde staan.
#. Vul bij **Identity settings** > **Identificatie handelende persoon-claim** de claim in die de identificatie
   bevat van de medewerker die namens het bedrijf inlogt.
#. Voer bij **LoA settings** > **claim path** het pad van de claim in (bijvoorbeeld
    ``authsp_level``) als die bekend is. Indien niet, kies dan bij
    **LoA settings** > **default** de waarde die meest van toepassing is. Dit wordt
    enkel gebruikt om vast te leggen met welk betrouwbaarheidsniveau iemand ingelogd is.
#. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus toevoegen,
    bijvoorbeeld:

    * klik op "Add item"
    * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``00`` op in het
      tekstveld
    * Selecteer "Non existent" in de **To** dropdown
    * Herhaal voor andere waarden en niveaus

Klik tot slot linksonder op **Opslaan**.

Je kan nu een formulier aanmaken met de ``eHerkenning via OpenID Connect``
authenticatie-plugin, zie :ref:`manual_forms_basics`.
