.. _manual_registration_stuf_zds:

========
StUF-ZDS
========

In de "StUF-ZDS"-plugin leidt de formulierinzending tot het aanmaken van een "Zaak" van
het ingestelde zaaktype. De aanvrager wordt als initiator geregistreerd bij de zaak, en
eventuele bijlagen/uploads worden als documenten ("Zaakinformatieobjecten") toegevoegd.

.. note:: De functioneel beheerder dient een aantal :ref:`koppelingen <configuration_registration_stufzds>`
   in te stellen om deze plugin te kunnen gebruiken.

Registratie-attributen
======================

Het merendeel van de :ref:`registratie-attributen <manual_form_fields_registration>` is
ondersteund in StUF-ZDS. Er gelden echter wat beperkingen.

**Initiator > adres**

Het adres van de initiator moet gevuld worden uit een "AdressNL"-component wat de
onderliggen attributen bevat. Je kan dus bijvoorbeeld niet een tekstveld registreren
met dit attribuut - hiervoor zijn meer specifieke attributen beschikbaar.
