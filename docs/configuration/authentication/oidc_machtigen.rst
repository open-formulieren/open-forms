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

    Verplicht indien ``DIGID_EHERKENNING_OIDC_STRICT`` op ``True`` staat.

.. _configuration_oidc_digid_machtigen_appgroup:

Configureren van OIDC-provider
------------------------------

De stappen hier zijn dezelfde als voor :ref:`configuration_oidc_digid_appgroup`.

.. warning:: Indien je de legacy **Redirect URI** gebruikt, dan is de waarde
   ``https://open-formulieren.gemeente.nl/digid-machtigen-oidc/callback/``.

Aan het eind van dit proces moet u de volgende gegevens hebben:

* Server adres, bijvoorbeeld ``login.gemeente.nl``
* Client ID, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``
* Client secret, bijvoorbeeld ``97d663a9-3624-4930-90c7-2b90635bd990``

Configureren van OIDC in Open Formulieren
-----------------------------------------

Om OIDC in Open-Formulieren te kunnen configureren zijn de volgende :ref:`gegevens <configuration_oidc_digid_machtigen_appgroup>` nodig:

* Server adres
* Client ID
* Client secret

Navigeer vervolgens in de admin naar **Configuratie** > **OpenID Connect configuration for DigiD Machtigen**.

#. Vink *Enable* aan om OIDC in te schakelen.
#. Vul bij **OpenID Connect client ID** het Client ID in, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``.
#. Vul bij **OpenID Connect secret** het Client secret in, bijvoobeeld ``97d663a9-3624-4930-90c7-2b90635bd990``.
#. Vul bij **OpenID Connect scopes**  ``openid``.
#. Vul bij **OpenID sign algorithm** ``RS256`` in.
#. Laat **Sign key** leeg.
#. Laat bij **Vertegenwoordigde claim name** de standaardwaarde staan, tenzij de naam van het BSN veld van de vertegenwoordigde in de OIDC claims anders is dan ``aanvrager.bsn``.
#. Laat bij **Gemachtigde claim name** de standaardwaarde staan, tenzij de naam van het BSN veld van de gemachtigde in de OIDC claims anders is dan ``gemachtigde.bsn``.

De endpoints die ingesteld moeten worden zijn dezelfde als voor DigiD. U kunt de stappen in :ref:`configuration_oidc_digid_appgroup`
volgen om die te configureren.

Nu kan er een formulier aangemaakt worden met het authenticatie backend ``DigiD Machtigen via OpenID Connect`` (zie :ref:`manual_forms_basics`).

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

    Verplicht indien ``DIGID_EHERKENNING_OIDC_STRICT`` op ``True`` staat.

``Service UUID``
    Het UUID van de dienst waarvoor de vertegenwoordiger gemachtigd is. Deze waarde staat
    in de dienstencatalogus.

    Verplicht indien ``DIGID_EHERKENNING_OIDC_STRICT`` op ``True`` staat.

.. _configuration_oidc_eh_bewindvoering_appgroup:

Configureren van OIDC-provider
------------------------------

De stappen hier zijn dezelfde als voor :ref:`configuration_oidc_digid_machtigen_appgroup`.

.. warning:: Indien je de legacy **Redirect URI** gebruikt, dan is de waarde
   ``https://open-formulieren.gemeente.nl/eherkenning-bewindvoering-oidc/callback/``.

Aan het eind van dit proces moet u de volgende gegevens hebben:

* OpenID connect client discovery endpoint, bijvoorbeeld ``https://keycloak-test.nl/auth/realms/zgw-publiek/``
* Client ID, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``
* Client secret, bijvoorbeeld ``97d663a9-3624-4930-90c7-2b90635bd990``
* Identity provider hint (optioneel)

Configureren van OIDC in Open Formulieren
-----------------------------------------

Om OIDC in Open-Formulieren te kunnen configureren zijn de volgende :ref:`gegevens <configuration_oidc_eh_bewindvoering_appgroup>` nodig:

* OpenID connect client discovery endpoint
* Client ID
* Client secret
* Identity provider hint (optioneel)

Navigeer vervolgens in de admin naar **Configuratie** > **OpenID Connect configuration for eHerkenning bewindvoering**.

#. Vink *Enable* aan om OIDC in te schakelen.
#. Vul bij **OpenID Connect client ID** het Client ID in, bijvoorbeeld ``a7d14516-8b20-418f-b34e-25f53c930948``.
#. Vul bij **OpenID Connect secret** het Client secret in, bijvoobeeld ``97d663a9-3624-4930-90c7-2b90635bd990``.
#. Vul bij **OpenID Connect scopes**  ``openid``.
#. Vul bij **OpenID sign algorithm** ``RS256`` in.
#. Laat **Sign key** leeg.
#. Laat bij **Vertegenwoordigd bedrijf claim name** de standaardwaarde staan, tenzij de naam van het KvK veld van de vertegenwoordigde in de OIDC claims anders is dan ``aanvrager.kvk``.
#. Laat bij **Gemachtigde persoon claim name** de standaardwaarde staan, tenzij de naam van het ID veld van de gemachtigde in de OIDC claims anders is dan ``gemachtigde.bsn``.
#. De endpoints die ingesteld moeten worden zijn dezelfde als voor DigiD. U kunt de stappen in :ref:`configuration_oidc_digid_appgroup` volgen om die te configureren.
#. Als u een Identity Provider hint heeft, dan vul het in. Voor Keycloak is dit nodig.

Nu kan er een formulier aangemaakt worden met het authenticatie backend ``eHerkenning bewindvoering via OpenID Connect`` (zie :ref:`manual_forms_basics`).
