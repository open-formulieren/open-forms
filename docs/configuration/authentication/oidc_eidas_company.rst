.. _configuration_authentication_oidc_eidas_company:

=====================================================
OpenID Connect voor inloggen met eIDAS voor bedrijven
=====================================================

Open Formulieren ondersteunt `eIDAS`_ (Electronic Identification and Trust Services)
login voor bedrijven via het OpenID Connect Protocol (OIDC).

`eIDAS`_ is een Europese Unie standaard, om europese inwoners en bedrijven naadloos
digitaal te laten identificeren in ieder europees land. Bij het authenticeren met eIDAS
worden enkele persoonsgegevens beschikbaar gesteld; de voor- en achternaam, geboortedatum
en de nationale identificatie van de ingelogde persoon. Voor authenticatie als bedrijf,
wordt daarnaast ook de officiële naam van het bedrijf beschikbaar gesteld.

Bedrijven kunnen op die manier inloggen op Open Formulieren met hun nationale
identificatie. In deze flow:

1. Klikt een gebruiker in een formulier op de knop *Inloggen met eIDAS voor bedrijven*
2. De gebruiker wordt via de omgeving van de OpenID Connect provider (bijv. Keycloak)
   naar eIDAS geleid, waar de gebruiker kan inloggen
3. eIDAS stuurt de gebruiker terug naar de OIDC omgeving, die op zijn beurt de gebruiker
   weer terugstuurt naar Open Formulieren
4. De gebruiker is ingelogd en kan verder met het invullen van het formulier

.. _configuration_oidc_eidas_company_claim_requirements:

Claim-eisen
===========

De OpenID Connect provider moet na een succesvolle login met eIDAS een aantal claims
aanbieden aan Open Formulieren. De precieze namen van deze claims kunnen ingesteld
worden in Open Formulieren.

``Claimnaam identificatie juridisch verantwoordelijke``
    De nationale identificatie van het bedrijf. Altijd verplicht.

``Claimnaam bedrijfsnaam juridisch verantwoordelijke``
    De officiële naam van het bedrijf. Altijd verplicht.

``Claimnaam BSN handelende persoon``
    Het BSN-nummer van de handelende persoon.

    Voor succesvolle authenticatie dient het BSN of de nationale identificatie
    aangeleverd te worden.

``Claimnaam nationale identificatie handelende persoon``
    De nationale identificatie van de handelende persoon. Dit wordt gebruikt voor
    personen die met een andere nationale identificerende waarde dan BSN inloggen, zoals
    een Deens identificatienummer.

    Voor succesvolle authenticatie dient het BSN of de nationale identificatie
    aangeleverd te worden.

``Claimnaam voornaam handelende persoon``
    De voornaam van de handelende persoon. Altijd verplicht.

``Claimnaam achternaam handelende persoon``
    De achternaam van de handelende persoon. Altijd verplicht.

``Claimnaam geboortedatum handelende persoon``
    De geboortedatum van de handelende persoon. Altijd verplicht.

``Betrouwbaarheidsniveau``
    Het betrouwbaarheidsniveau gebruikt tijdens het inloggen. Dit wordt vastgelegd en
    meegestuurd tijdens het registeren van formulierinzendingen. Als de provider dit
    niet kan aanleveren, dan kan je een standaardwaarde instellen in Open Formulieren.

    Beheerders kunnen waardenvertalingen inrichten indien de provider de waarden
    niet aanlevert zoals gedocumenteerd in de koppelvlakstandaard van Logius.

.. _configuration_oidc_eidas_company_appgroup:

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

Zorg dat je de volgende :ref:`gegevens <configuration_oidc_eidas_company_appgroup>` hebt:

* Server adres
* Client ID
* Client secret

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC Providers** >
**eidas-company-oidc-provider**.

Hier kan je de endpoints van de OIDC provider inrichten. Deze kunnen automatisch
bepaald worden aan de hand van het discovery endpoint
(``https://login.gemeente.nl/auth/realms/{realm}/.well-known/openid-configuration``).

#. Vul bij **Discovery endpoint** het pad naar het juiste authenticatie realm endpoint
    van de OpenID Connect provider in (met een ``/`` op het einde),
    bijvoorbeeld ``https://login.gemeente.nl/auth/realms/{realm}/``.
#. Laat de overige endpoints leeg - deze worden automatisch aangevuld.

Navigeer vervolgens in de admin naar **Configuratie** > **OIDC Clients** > **eidas-oidc**.

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

Stel dan de eIDAS specifieke instellingen in de **opties** veld:

#. Vul bij **Identity settings** > **Claimnaam identificatie juridisch verantwoordelijke**
   de claim in die de nationale identificatie van het bedrijf bevat.
#. Vul bij **Identity settings** > **Claimnaam bedrijfsnaam juridisch verantwoordelijke**
   de claim in die de officiële naam van het bedrijf bevat.
#. Vul bij **Identity settings** > **Claimnaam BSN handelende persoon** de claim in die
   het BSN-nummer van de handelende persoon bevat, bijvoorbeeld ``sub``.
#. Vul bij **Identity settings** > **Claimnaam nationale identificatie handelende persoon**
   de claim in die de nationale identificatie van de handelende persoon bevat.
#. Vul bij **Identity settings** > **Claimnaam voornaam handelende persoon** de claim in
   die de voornaam van de handelende persoon bevat.
#. Vul bij **Identity settings** > **Claimnaam achternaam handelende persoon** de claim
   in die de achternaam van de handelende persoon bevat.
#. Vul bij **Identity settings** > **Claimnaam geboortedatum handelende persoon** de
   claim in die de geboortedatum van de handelende persoon bevat.
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

Je kan nu een formulier aanmaken met de ``eIDAS voor bedrijven via OpenID Connect``
authenticatie-plugin, zie :ref:`manual_forms_basics`.


.. _`eIDAS`: https://www.logius.nl/diensten/eidas
