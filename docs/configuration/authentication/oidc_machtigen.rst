.. _configuration_authentication_oidc_machtigen:

=============================================================================
OpenID Connect voor inloggen met DigiD Machtigen en eHerkenning bewindvoering
=============================================================================

Open Formulieren ondersteunt `DigiD Machtigen`_ en eHerkenning bewindvoering login voor
burgers via het OpenID Connect protocol (OIDC). Burgers kunnen inloggen op Open
Formulieren met hun DigiD/eHerkenning account en een formulier invullen namens iemand
anders. In deze flow:

* Een gebruiker klikt op de knop *Inloggen met DigiD Machtigen* of *Inloggen met
  eHerkenning bewindvoering* die op de startpagina van een formulier staat.
* De gebruiker wordt via de omgeving van de OpenID Connect provider (bijv. `Keycloak`_)
  naar DigiD/eHerkenning geleid, waar de gebruiker kan inloggen met *hun eigen*
  DigiD/eHerkenning inloggegevens.
* De gebruiker kan dan kiezen namens wie ze het formulier willen invullen.
* De gebruiker wordt daarna terug naar de OIDC omgeving gestuurd, die op zijn beurt de
  gebruiker weer terugstuurt naar Open Formulieren
* De gebruiker kan verder met het invullen van het formulier

.. _DigiD Machtigen: https://machtigen.digid.nl/
.. _Keycloak: https://www.keycloak.org/

DigiD Machtigen
===============

Claim-eisen
-----------

``BSN vertegenwoordiger``
    Het BSN van de vertegenwoordiger die "aan de knoppen zit". Altijd verplicht.

``BSN vertegenwoordigde``
    Het BSN van de vertegenwoordigde gebruiker. Altijd verplicht.

``betrouwbaarheidsniveau``
    Het betrouwbaarheidsniveau gebruikt tijdens het inloggen. Dit wordt vastgelegd en
    meegestuurd tijdens het registeren van formulierinzendingen. Als de provider dit
    niet kan aanleveren, dan kan je een standaardwaarde instellen in Open Formulieren.

    Beheerders kunnen waardenvertalingen inrichten indien de provider de waarden
    niet aanlevert zoals gedocumenteerd in de koppelvlakstandaard van Logius.

``Service ID``
    Het ID van de dienst waarvoor de vertegenwoordiger gemachtigd is. Dit komt voor de
    provider/broker beschikbaar via Logius' DigiD Machtigen.

    Verplicht indien ``DIGID_EHERKENNING_OIDC_STRICT`` (:ref:`installation_environment_config`) op ``True`` staat.

.. _configuration_oidc_digid_machtigen_appgroup:

Configureren van OIDC-provider
------------------------------

Contacteer de IAM beheerders in je organisatie om een *Client* aan te
maken in de omgeving van de OpenID Connect provider.

**Redirect URI (vanaf Open Formulieren 2.7.0)**

.. versionchanged:: 3.0

    Open Forms no longer uses the legacy endpoints by default.

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/auth/oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein.

**Redirect URI (legacy)**

Voor de **Redirect URI** vul je ``https://open-formulieren.gemeente.nl/digid-machtigen-oidc/callback/`` in,
waarbij je ``open-formulieren.gemeente.nl`` vervangt door het relevante domein.

**Gegevens**

Aan het eind van dit proces moet je de volgende gegevens hebben:

* Server adres, bijvoorbeeld ``login.gemeente.nl``
* Client ID, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``
* Client secret, bijvoorbeeld ``97d663a9-3624-4930-90c7-2b90635bd990``

Configureren van OIDC in Open Formulieren
-----------------------------------------

Om OIDC in Open-Formulieren te kunnen configureren zijn de volgende
:ref:`gegevens <configuration_oidc_digid_machtigen_appgroup>` nodig:

* Server adres
* Client ID
* Client secret

Navigeer vervolgens in de admin naar **Configuratie** > **DigiD Machtigen (OIDC)**.

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

.. note:: Indien er sprake is van *nesting* in de claims, voeg dan een regel toe met het
   plusje voor elk niveau.

7. Vul bij **BSN vertegenwoordigde-claim** de naam van de claim in die het BSN bevat
   van de machtiger, bijvoorbeeld ``aanvrager.bsn``.
8. Vul bij **BSN vertegenwoordiger-claim** de naam van de claim in die het BSN bevat
   van de gemachtigde, bijvoorbeeld ``gemachtigde.bsn``.
9. Voer bij **betrouwbaarheidsniveau-claim** de naam van de claim in (bijvoorbeeld
   ``authsp_level``) als die bekend is. Indien niet, kies dan bij
   **Standaardbetrouwbaarheidsniveau** de waarde die meest van toepassing is. Dit wordt
   enkel gebruikt om vast te leggen met welk betrouwbaarheidsniveau iemand ingelogd is.
10. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus toevoegen,
    bijvoorbeeld:

    * klik op "Add item"
    * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``10`` op in het
      tekstveld
    * Selecteer "DigiD Basis" in de **To** dropdown
    * Herhaal voor andere waarden en niveaus
11. Vul bij de **Service ID-claim** de naam van de claim in die aangeeft voor welke
    dienst de machtiging afgegeven is, bijvoobeeld ``urn:nl-eid-gdi:1.0:ServiceUUID``.

De endpoints die ingesteld moeten worden zijn dezelfde als voor DigiD. Je kan de stappen
in :ref:`configuration_oidc_digid_appgroup` volgen om die te configureren.

Je kan nu een formulier aanmaken met de ``DigiD Machtigen via OpenID Connect``
authenticatie-plugin, zie :ref:`manual_forms_basics`.

eHerkenning bewindvoering
=========================

Claim-eisen
-----------

Alle eisen voor :ref:`standaard-eHerkenning <configuration_oidc_eherkenning_claim_requirements>`
gelden, plus:

``BSN vertegenwoordigde``
    Het BSN van de vertegenwoordigde gebruiker. Altijd verplicht.

``Service ID``
    Het ID van de dienst waarvoor de vertegenwoordiger gemachtigd is. Deze waarde staat
    in de dienstencatalogus.

    Verplicht indien ``DIGID_EHERKENNING_OIDC_STRICT`` (:ref:`installation_environment_config`) op ``True`` staat.

``Service UUID``
    Het UUID van de dienst waarvoor de vertegenwoordiger gemachtigd is. Deze waarde staat
    in de dienstencatalogus.

    Verplicht indien ``DIGID_EHERKENNING_OIDC_STRICT`` (:ref:`installation_environment_config`) op ``True`` staat.

.. _configuration_oidc_eh_bewindvoering_appgroup:

Configureren van OIDC-provider
------------------------------

De stappen hier zijn dezelfde als voor :ref:`configuration_oidc_eherkenning_appgroup`.

.. warning:: Indien je de legacy **Redirect URI** gebruikt, dan is de waarde
   ``https://open-formulieren.gemeente.nl/eherkenning-bewindvoering-oidc/callback/``.

Aan het eind van dit proces moet u de volgende gegevens hebben:

* OpenID connect client discovery endpoint, bijvoorbeeld ``https://keycloak-test.nl/auth/realms/zgw-publiek/``
* Client ID, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``
* Client secret, bijvoorbeeld ``97d663a9-3624-4930-90c7-2b90635bd990``
* Identity provider hint (optioneel)

Configureren van OIDC in Open Formulieren
-----------------------------------------

Om OIDC in Open-Formulieren te kunnen configureren zijn de volgende
:ref:`gegevens <configuration_oidc_eh_bewindvoering_appgroup>` nodig:

* OpenID connect client discovery endpoint
* Client ID
* Client secret
* Identity provider hint (optioneel)

Navigeer vervolgens in de admin naar **Configuratie** > **eHerkenning bewindvoering (OIDC)**.

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

7. Vul bij **Identificatie vertegenwoordigde-claim** de naam van de claim in die het
   BSN bevat van de machtiger, bijvoorbeeld ``bsn``.
8. Vul bij **Soort identificatie-claim** de claim in die aangeeft of het een KVK-nummer
   of RSIN betreft (merk op: op dit moment ondersteunen we enkel KVK). Indien onbekend,
   dan kan je de standaardwaarde laten staan.
9. Vul bij **Bedrijfsidenticatie-claim** de claim in die het KVK-nummer (of RSIN,
   toekomst) bevat, bijvoorbeeld ``kvk``.
10. Vul de claim in die het (eventuele) vestigingsnummer bevat bij
    **Vestigingsnummer-claim**. Indien onbekend, laat dan de standaardwaarde staan.
11. Vul bij **Identificatie handelende persoon-claim** de claim in die de identificatie
    bevat van de medewerker die namens het bedrijf inlogt.
12. Voer bij **betrouwbaarheidsniveau-claim** de naam van de claim in (bijvoorbeeld
    ``authsp_level``) als die bekend is. Indien niet, kies dan bij
    **Standaardbetrouwbaarheidsniveau** de waarde die meest van toepassing is. Dit wordt
    enkel gebruikt om vast te leggen met welk betrouwbaarheidsniveau iemand ingelogd is.
13. Indien gewenst, dan kan je waardenvertalingen voor de betrouwbaarheidsniveaus toevoegen,
    bijvoorbeeld:

    * klik op "Add item"
    * Kies "Tekstuele waarde" in de **From** dropdown en voer de waarde ``00`` op in het
      tekstveld
    * Selecteer "Non existent" in de **To** dropdown
    * Herhaal voor andere waarden en niveaus

De endpoints die ingesteld moeten worden zijn dezelfde als voor DigiD. Je kan de stappen
in :ref:`configuration_oidc_eherkenning_appgroup` volgen om die te configureren.

Je kan nu een formulier aanmaken met de ``eHerkenning bewindvoering via OpenID Connect``
authenticatie-plugin, zie :ref:`manual_forms_basics`.
