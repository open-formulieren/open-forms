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

Het standaardgedrag van Open Formulieren is dat het een :ref:`publieke referentie <manual_submissions_public_reference>`
genereert en deze vervolgens als zaaknummer gebruikt bij het aanmaken van een zaak in de Zaken API.

ZGW API's kunnen zelf zaaknummers genereren, en deze nummers worden gebruikt voor de publieke
referentie van de aanvraag. Navigeer hiervoor naar:
**Admin** > **Configuratie** > **Configuratie overzicht** > **Registratieplugins**. Vind
hierbinnen het label "ZGW API's" en klik op **API-groepen beheren**. Selecteer in lijst
van API-groepen de gewenste groep en klik de naam aan om het bewerkscherm te openen.
Vink vervolgens de optie **Gebruik gegenereerd zaaknummer** aan en sla de wijzigingen
op.

.. note:: Indien je onvoldoende rechten hebt, vraag dan een functioneel beheerder om
   deze instelling aan te passen.
