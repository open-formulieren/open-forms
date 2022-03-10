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

.. _configuration_oidc_eherkenning_appgroup:

Configureren van OIDC voor eHerkenning
======================================

Contacteer de IAM beheerders in je organisatie om een *Client* aan te
maken in de omgeving van de OpenID Connect provider.

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/eherkenning-oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein.

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

Navigeer vervolgens in de admin naar **Configuratie** > **OpenID Connect configuration for eHerkenning**.

1. Vink *Enable* aan om OIDC in te schakelen.
2. Laat bij **KVK claim name** de standaardwaarde staan, tenzij de naam van het KVK-nummer veld
   in de OIDC claims anders is dan ``kvk``.
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

Nu kan er een formulier aangemaakt worden met het authenticatie backend ``eHerkenning via OpenID Connect``, zie :ref:`manual_forms_basics`.
