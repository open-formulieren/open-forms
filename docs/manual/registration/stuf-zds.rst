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

Leverancierspecifieke opmerkingen
=================================

Sommige leveranciers van systemen die StUF-ZDS spreken vereisen wat extra aandacht.

.. tip:: Mis je een leverancier hier? Laat het ons weten in een
   `Github issue <https://github.com/open-formulieren/open-forms/issues>`_.

Onegov 365 zaaksysteem
----------------------

``<ZKN:startdatum>`` ondersteuning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Onegov verwacht in dit element een datumtijd in plaats van een datum. Echter, de
VNG-standaard schrijft een datum zonder tijdselement voor.

Je kan hieromheen werken met een ``extraElement``-mapping in de
formulierregistratie-opties. Zorg dat er een koppeling is tussen de formuliervariabele
"Inzendingsvoltooiingsdatum" (``completed_on``) met de elementnaam ``zaak.pv_startdatum``.

Betalingsinformatie
^^^^^^^^^^^^^^^^^^^

Open Forms maakt gebruik van de  StUF-ZDS elementen ``<ZKN:betalingsIndicatie>`` en
``<ZKN:laatsteBetaaldatum>`` om de betaalstatus te communiceren.. Onegov verwacht extra
informatie die niet beschikbaar is via de StUF-ZDS-standaard in een aantal
``extraElementen``:

* ``zaak.pv_orderid``: de registratievariabele "Publieke order-ID's van betaling"
  (``payment_public_order_ids``) bestaat hiervoor. Je moet de optie "Door komma's
  gescheiden waarden" inschakelen zodat Onegov dit begrijpt - anders worden meerdere
  elementen opgenomen die elk een ``.$index``-achtervoegsel bevatten.

  .. note:: Beheerders kunnen het sjabloon voor deze ID's instellen. Houd er rekening
     mee dat Onegov een limiet heeft van 100 karakters op de waarde van dit element.
     Vooral als een inzending meerdere Order-ID's heeft, kan dit problemen
     veroorzaken.

* ``zaak.pv_bedrag``: je kan de registratievariabele "Betalingsbedrag"
  (``payment_amount``) koppelen aan deze naam. Deze gebruikt een punt (``.``) als
  decimaal scheidingsteken, zoals Onegov dit verwacht.

* ``zaak.pv_betaalmethode``: dit laat je best weg - Open Formulieren maakt gebruik van
  Payment providers die dit regelen en wij kennen dus de betaalmethode niet.

* ``zaak.pv_transactieid``: de gegevens hiervoor zitten in de "Provider betaling-ID's"
  variabele (``provider_payment_ids``), en heeft dezelfde beperkingen als
  ``zaak.pv_orderid``.

* ``zaak.pv_betaalstatus``: kan niet gekoppeld worden, maar het StUF-ZDS-element
  ``<ZKN:betalingsIndicatie>`` is de juiste plaats voor dit gegeven, wat Open
  Formulieren al automatisch meestuurt.

Contactgegevens
^^^^^^^^^^^^^^^

Open Formulieren gebruikt het StUF-ZDS element ``heeftAlsAanspreekpunt`` om de
contactgegevens van de initiator mee te sturen. Onegov ondersteunt dit element niet,
maar we hebben hiervoor een workaround via ``extraElement`` koppelingen op het niveau
van de initiator.

Ga in de plugin-instellingen naar de tab "Extra elementen" en voeg koppelingen toe onder
de kop "Variabelekoppelingen (initiator)". De StUF-namen die Onegov verwacht zijn:

* ``pv_afwijkendtelefoon``: kies de formuliervariabele die het telefoonnnummer bevat.
* ``pv_emailafwijkend``: kies de formuliervariabele die het e-mailadres bevat.
