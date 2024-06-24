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

.. warning::

    Zorg dat Open Formulieren :ref:`geïnstalleerd <installation_index>` is met de
    ``USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS=false``
    :ref:`omgevingsvariabele<installation_environment_config>`, anders worden de legacy
    (zie hieronder) endpoints gebruikt.

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

Navigeer vervolgens in de admin naar **Configuratie** > **OpenID Connect configuration for DigiD**.

1. Vink *Enable* aan om OIDC in te schakelen.
2. Laat bij **BSN claim name** de standaardwaarde staan, tenzij de naam van het BSN veld
   in de OIDC claims anders is dan ``bsn``.
3. Vul bij **OpenID Connect client ID** het Client ID in, bijvoorbeeld
   ``a7d14516-8b20-418f-b34e-25f53c930948``.
4. Vul bij **OpenID Connect secret** het Client secret in, bijvoobeeld
   ``97d663a9-3624-4930-90c7-2b90635bd990``.
5. Laat bij **OpenID Connect scopes** de standaardwaarden staan.
6. Vul bij **OpenID sign algorithm** ``RS256`` in.
7. Laat **Sign key** leeg.

Vervolgens moeten er een aantal endpoints van de OIDC provider ingesteld worden,
deze kunnen automatisch bepaald worden aan de hand van het discovery endpoint
(``https://login.gemeente.nl/auth/realms/{realm}/.well-known/openid-configuration``).

7. Vul bij **Discovery endpoint** het pad naar het juiste authenticatie realm endpoint
   van de OpenID Connect provider in (met een `/` op het einde),
   meestal is dit ``https://login.gemeente.nl/auth/realms/{realm}/``.
8. Laat de overige endpoints leeg.

Klik tot slot rechtsonder op **Opslaan**.

Nu kan er een formulier aangemaakt worden met het authenticatie backend ``DigiD via OpenID Connect``, zie :ref:`manual_forms_basics`.
