.. _configuration_authentication_oidc_digid:

======================================
OpenID Connect voor inloggen met DigiD
======================================

Open Formulieren ondersteunt DigiD login voor burgers via het OpenID Connect protocol (OIDC).

Burgers kunnen op die manier inloggen op Open Formulieren met hun DigiD account. In deze
flow:

1. Klikt een gebruiker in een formulier op de knop *Inloggen met DigiD*
2. De gebruiker wordt via de omgeving van de OpenID Connect provider (bijv. Keycloak) naar DigiD geleid,
   waar de gebruiker kan inloggen
3. DigiD stuurt de gebruiker terug naar de OIDC omgeving, die op zijn beurt de gebruiker weer terugstuurt naar Open Formulieren
4. De gebruiker is ingelogd en kan verder met het invullen van het formulier

.. _configuration_oidc_digid_claim_requirements:

Claim-eisen
===========

De OpenID Connect provider moet na een succesvolle login met DigiD een aantal claims
aanbieden aan Open Formulieren. De precieze namen van deze claims kunnen ingesteld
worden in Open Formulieren.

``BSN``
    Het BSN van de ingelogde gebruiker. Altijd verplicht.

``betrouwbaarheidsniveau``
    Het betrouwbaarheidsniveau gebruikt tijdens het inloggen. Dit wordt vastgelegd en
    meegestuurd tijdens het registeren van formulierinzendingen. Als de provider dit
    niet kan aanleveren, dan kan je een standaardwaarde instellen in Open Formulieren.

    Beheerders kunnen waardenvertalingen inrichten indien de provider de waarden
    niet aanlevert zoals gedocumenteerd in de koppelvlakstandaard van Logius.

.. _configuration_oidc_digid_appgroup:

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

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/digid-oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein.

**Gegevens**

Aan het eind van dit proces moet je de volgende gegevens hebben:

* Server adres, bijvoorbeeld ``login.gemeente.nl``
* Client ID, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``
* Client secret, bijvoorbeeld ``97d663a9-3624-4930-90c7-2b90635bd990``

Configureren van OIDC in Open Formulieren
=========================================

Zorg dat je de volgende :ref:`gegevens <configuration_oidc_digid_appgroup>` hebt:

* Server adres
* Client ID
* Client secret

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC provider** > **oidc-digid-provider**.

Hier kan je de endpoints van de OIDC provider inrichten. Deze kunnen automatisch
bepaald worden aan de hand van het discovery endpoint
(``https://login.gemeente.nl/auth/realms/{realm}/.well-known/openid-configuration``).

#. Vul bij **Discovery endpoint** het pad naar het juiste authenticatie realm endpoint
   van de OpenID Connect provider in (met een ``/`` op het einde),
   bijvoorbeeld ``https://login.gemeente.nl/auth/realms/{realm}/``.
#. Laat de overige endpoints leeg - deze worden automatisch aangevuld.

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC clients** > **oidc-digid**.

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

Stel dan de DigiD specifieke instellingen in de **opties** veld:

#. Laat bij **Identity settings** > **BSN claim path** de standaardwaarde staan, tenzij het pad van het BSN veld
   in de OIDC claims anders is dan ``bsn``.
#. Voer bij **LoA settings** > **claim path** het pad van de claim in (bijvoorbeeld
   ``authsp_level``) als die bekend is. Indien niet, kies dan bij
   **LoA settings** > **Default** de waarde die meest van toepassing is. Dit wordt
   enkel gebruikt om vast te leggen met welk betrouwbaarheidsniveau iemand ingelogd is.
#. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus toevoegen,
   bijvoorbeeld:

   * klik op "Add item"
   * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``10`` op in het
     tekstveld
   * Selecteer "DigiD Basis" in de **To** dropdown
   * Herhaal voor andere waarden en niveaus

Klik tot slot linksonder op **Opslaan**.

Je kan nu een formulier aanmaken met de ``DigiD via OpenID Connect``
authenticatie-plugin, zie :ref:`manual_forms_basics`.
