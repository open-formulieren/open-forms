.. _configuration_authentication_oidc:

==============
OpenID Connect
==============

.. note::

  This page documents how to set up Single Sign on (SSO) for admins, to access 
  the management interface. If you are looking to authenticate organization 
  members on forms, please go 
  :ref:`here <configuration_authentication_oidc_org>`.

Open Formulieren ondersteunt Single Sign On (SSO) via het OpenID Connect protocol (OIDC) voor de beheerinterface.

Gebruikers kunnen op die manier inloggen op Open Formulieren met hun account bij de OpenID Connect provider. In deze
flow:

1. Klikt een gebruiker op het inlogscherm op *Inloggen met organisatieaccount*
2. De gebruiker wordt naar de omgeving van de OpenID Connect provider geleid (bijv. Keycloak) waar ze inloggen met gebruikersnaam
   en wachtwoord (en eventuele Multi Factor Authentication)
3. De OIDC omgeving stuurt de gebruiker terug naar Open Formulieren (waar de account aangemaakt
   wordt indien die nog niet bestaat)
4. Een beheerder in Open Formulieren kent de juiste groepen toe aan deze gebruiker als deze
   voor het eerst inlogt.

.. note:: Standaard krijgen deze gebruikers **geen** toegang tot de beheerinterface. Deze
   rechten moeten door een (andere) beheerder ingesteld worden. De
   account is wel aangemaakt.

.. _configuration_oidc_appgroup:

Configureren van OIDC-provider
==============================

Contacteer de IAM beheerders in je organisatie om een *Client* of *App* aan te
maken in de omgeving van de OpenID Connect provider.

**Redirect URI (vanaf Open Formulieren 2.7.0)**

.. versionchanged:: 3.0

    Open Forms no longer uses the legacy endpoints by default.

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/auth/oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein. Deze
Redirect URI wordt ook gebruikt voor :ref:`configuration_authentication_oidc_org`.

**Redirect URI (legacy)**

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein.

Als je gebruikers van dezelfde organisatie ook wilt laten inloggen op 
formulieren, voeg dan ook direct 
``https://open-formulieren.gemeente.nl/oidc-org/callback/`` toe. Je kan hier 
meer over lezen op :ref:`configuration_authentication_oidc_org`.

**Gegevens**

Aan het eind van dit proces moet je de volgende gegevens hebben (on premise):

* Server adres, bijvoorbeeld ``login.gemeente.nl``
* Client ID, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``
* Client secret, bijvoorbeeld ``97d663a9-3624-4930-90c7-2b90635bd990``
* Discovery endpoint, bijvoorbeeld ``https://login.microsoftonline.com/9c6a25fb-3f9a-4e8b-aa84-b7e2252bcc87/v2.0/.well-known/openid-configuration``

Configureren van OIDC in Open Formulieren
=========================================

Zorg dat je de volgende :ref:`gegevens <configuration_oidc_appgroup>` hebt:

* Server adres
* Client ID
* Client secret
* Discovery endpoint

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC provider** > **oidc-admin-provider**.

Hier kan je de endpoints van de OIDC provider inrichten. Deze kunnen automatisch
bepaald worden aan de hand van het discovery endpoint
(``https://login.gemeente.nl/auth/realms/{realm}/.well-known/openid-configuration``).

#. Vul bij **Discovery endpoint** het pad naar het juiste authenticatie realm endpoint
   van de OpenID Connect provider in (met een ``/`` op het einde),
   bijvoorbeeld ``https://login.gemeente.nl/auth/realms/{realm}/``.
#. Laat de overige endpoints leeg - deze worden automatisch aangevuld.

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC clients** > **oidc-admin**.

#. Vink *Enable* aan om OIDC in te schakelen.
#. Selecteer de provider die je net heb geconfigureerd in de **OIDC Provider** dropdown.
#. Vul bij **OpenID Connect client ID** het Client ID in, bijvoorbeeld
   ``a7d14516-8b20-418f-b34e-25f53c930948``.
#. Vul bij **OpenID Connect secret** het Client secret in, bijvoobeeld
   ``97d663a9-3624-4930-90c7-2b90635bd990``.
#. Laat bij **OpenID Connect scopes** de standaardwaarden staan.
#. Vul bij **OpenID sign algorithm** ``RS256`` in.
#. Laat **Sign key** leeg.

Klik tot slot rechtsonder op **Opslaan**.

Je kan vervolgens het makkelijkst testen of alles werkt door in een incognitoscherm
naar ``https://open-formulieren.gemeente.nl/admin/`` te navigeren en op 
*Inloggen met organisatieaccount* te klikken.

.. note:: We raden aan om Open Formulieren te deployen met de ``USE_OIDC_FOR_ADMIN_LOGIN=1``
   environment variabele zodat je meteen omgeleid wordt naar de OpenID Connect Provider.
