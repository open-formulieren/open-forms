.. _manual_registration_zgw_apis:

=========
ZGW API's
=========

In de "Zaakgericht Werken API's"-plugin (ZGW API's) leidt de formulierinzending tot het
aanmaken van een "Zaak" van het ingestelde zaaktype. De aanvrager wordt als initiator
geregistreerd bij de zaak, en eventuele bijlagen/uploads worden als documenten
("Zaakinformatieobjecten") toegevoegd.

.. note:: De functioneel beheerder dient een aantal :ref:`koppelingen <configuration_registration_zgw>`
   in te stellen om deze plugin te kunnen gebruiken.

Zaaknummers
===========

Het standaardgedrag van Open Formulieren is dat het een :ref:`publieke referentie
<manual_submissions_public_reference>` genereert en deze vervolgens als zaaknummer
gebruikt bij het aanmaken van een zaak in de Zaken API.

ZGW API's kunnen zelf zaaknummers genereren, en deze nummers worden gebruikt voor de
publieke referentie van de aanvraag. Navigeer hiervoor naar:
**Admin** > **Configuratie** > **Configuratie overzicht** > **Registratieplugins**. Vind
hierbinnen het label "ZGW API's" en klik op **API-groepen beheren**. Selecteer in lijst
van API-groepen de gewenste groep en klik de naam aan om het bewerkscherm te openen.
Vink vervolgens de optie **Gebruik gegenereerd zaaknummer** aan en sla de wijzigingen
op.

.. note:: Indien je onvoldoende rechten hebt, vraag dan een functioneel beheerder om
   deze instelling aan te passen.

Zaakomschrijving en toelichting
===============================

De "Omschrijving"- en "Toelichting"-opties ondersteunen sjablonen. Voor meer details
over welke variabelen en expressis beschikbaar zijn, ga naar :ref:`zgw_api_registratie`.

Documenten
==========

Aan de zaak worden standaard een aantal documenten toegevoegd als zaakdocumenten:

* De bevestigings-PDF met de inzendingsgegevens.
* De bevestigingsmail die verstuurd is naar de inzender.
* Alle bestanden die door de gebruiker toegevoegd zijn in "Bestandsupload"-velden.

Gebruikersbijlagen
------------------

Bestanden die toegevoegd zijn door de gebruiker in "Bestandsupload"-velden worden
geüpload naar de Documenten API en aan de zaak gerelateerd.

In de plugin-instellingen kan je een catalogus selecteren en vervolgens kies je het
standaard-documenttype wat voor dergelijke bijlagen gebruikt dient te worden. Per
"Bestandsupload"-veld kan je hiervan afwijken, indien nodig. Ga hiervoor in de
formulierinstellingen naar de "Variabelen" tab. Daarbinnen vind je een bewerk-icoon in
de "Registratie"-kolom om instellingen voor specifieke bestanduploadvelden aan te
passen.

.. versionchanged:: 4.0.0

    Sinds Open Formulieren 4.0.0 kan je de registratie-instellingen niet meer in het
    veld zelf instellen, maar moet dit via de "Variabelen"-tab.

Registratie-attributen
======================

Het merendeel van de :ref:`registratie-attributen <manual_form_fields_registration>` is
ondersteund in de ZGW APIs. Er gelden echter wat beperkingen.

**Initiator > adres**

Het adres van de initiator moet gevuld worden uit een "AdressNL"-component wat de
onderliggen attributen bevat. Je kan dus bijvoorbeeld niet een tekstveld registreren
met dit attribuut - hiervoor zijn meer specifieke attributen beschikbaar.

Daarnaast is er een verschil tussen burgers, bedrijven en vestigingen:

* voor burgers wordt het verblijfsadres gevuld, waarvan de plaatsnaam en openbare
  ruimtenaam (straatnaam) meegegeven moeten worden. Dit vereist dat de optie
  "Adres afleiden" ingeschakeld is.
* voor vestigingen geldt dezelfde beperking.
* voor niet-natuurijke personen (bedrijven, zonder vestiging) wordt het bezoekadres
  gevuld en geldt deze beperking niet.
