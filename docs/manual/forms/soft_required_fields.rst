.. _manual_forms_soft_required_fields:

=================================================
Formuliervelden met niet-blokkerende verplichting
=================================================

Sommige velden laten toe om ze als "aangeraden" te markeren. In deze configuratie wordt
de gebruiker er van bewust gemaakt dat ze velden onbedoeld leeg laten, maar het blokkeert
ze niet om het formulier in te zenden.

.. note:: De meeste formuliervelden ondersteunen een
   :ref:`validatie-optie <manual_form_fields_validation>` om het veld verplicht te
   maken. Deze kan echter soms (om juridische redenen) niet gebruikt worden omdat een
   gebruiker de aanvraag móet kunnen insturen en de organisatie verplicht is om
   deze te beoordelen. Het is dan netjes om de gebruiker te kunnen wijzen op eventuele
   kosten en gevolgen van het niet aanleveren van alle uitgevraagde gegevens.

Formulierconfiguratie
=====================

.. note:: Deze documentatie gaat ervan uit dat je bekend met de basis van
   :ref:`formulieren beheren <manual_forms_basics>`.

Het is belangrijk dat je in de betreffende formulierstap(pen) een component toevoegt
die de foutmeldingen weergeeft, anders krijgt de gebruiker geen feedback van eventuele
ontbrekende gegevens.

Voor elke relevante formulierstap:

1. Sleep zoals je gewend bent de velden uit het menu aan de linkerkant, en stel de
   relevante configuraties in.
2. In het instellingenscherm, klik op de "Validatie"-tab.
3. Schakel vervolgens het selectievakje "Aangeraden (niet-blokkerend verplicht)" in.
   Indien je deze niet kan aanvinken, controleer dan dat de optie "Verplicht" uitgevinkt
   is - een veld kan namelijk niet tegelijk blokkerend en niet-blokkerend verplicht zijn.
4. Sla de veldinstellingen op.
5. Herhaal stap 1 tot en met 4 voor alle benodigde velden.
6. Klik in het menu aan de linkerkant de categorie "Opmaak" open.
7. Sleep het component "Foutmeldingen aangeraden velden" in de formulierstap.

    * De inhoud zal enkel getoond worden als er "aangeraden velden" een lege waarde
      hebben.
    * Je kan het bericht voor de gebruiker naar wens instellen. Hierin kan je de
      sjabloonvariabele ``{{ missingFields }}`` gebruiken die getoond wordt als lijst
      van veld-labels met ontbrekende waarde.
    * Andere sjabloonvariabelen of -uitdrukkingen kunnen niet gebruikt worden.
    * Je kan hier ook vertalingen toepassen.

Ondersteunde velden
===================

De velden die "Aangeraden (niet-blokkerend verplicht)"-validatie ondersteunen zijn:

* Bestandsupload

Neem contact op indien je deze functionaliteit ook bij andere veldsoorten wenst.
