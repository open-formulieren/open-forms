.. _manual_cosign_flow:

=================
Mede-ondertekenen
=================

Open Formulieren ondersteunt formulieren waarin een tweede persoon een inzending moet
ondertekenen voor deze verwerkt wordt, zoals een partner of voogd. Er is dus een extra
persoon betrokken naast de invuller van het formulier.

Het mede-ondertekenproces kent twee varianten, afhankelijk van de precieze
:ref:`algemene configuratie <configuration_general_cosign>` ingesteld door een
beheerder. Voor beide varianten dien je een "mede-onderteken"-component in het
formulier toe te voegen om mede-ondertekenen te activeren.

We beschrijven twee persona:

* de klant: de persoon die het formulier initieel start en invult
* de ondertekenaar: de persoon die de inzending mede moet ondertekenen

.. note:: De condities waarin een mede-ondertekening vereist is, zijn:

    * het formulier bevat een mede-ondertekenencomponent
    * het mede-ondertekenencomponent is verplicht (tabje validatie) óf het is
      niet-verplicht, maar de gebruiker vult een e-mailadres in bij het optionele veld

    Als mede-ondertekenen vereist is, dan worden mede-ondertekeningspecifieke sjablonen
    geselecteerd in plaats van de algemene sjablonen.

Met links in emails
===================

#. De klant navigeert naar het formulier, waar de inlogopties zoals gebruikelijk
   zichtbaar zijn. Er zijn geen "mede-ondertekeneninlogopties".
#. De klant logt in en vult het formulier in.
#. Bij het "mede-onderteken"-component vult de klant het e-mailadres van de
   ondertekenaar in.
#. Zodra het formulier ingestuurd wordt, worden e-mails verstuurd:

   * de klant krijgt een bevestigingsmail (als deze inschakeld is)
   * de ondertekenaar krijgt een e-mail met het ondertekenverzoek, waarin de
     formulierlink staat

#. De ondertekenaar klikt op de link in de email en krijgt een startscherm met uitleg
   over het mede-ondertekenen.
#. De ondertekenaar logt in en ziet vervolgens een overzicht van de ingevulde gegevens.
   Indien relevant accepteert die de verklaring van waarheid en/of privacybeleid. Daarna
   bevestigt die de mede-ondertekening.
#. De klant en de ondertekenaar ontvangen allebei een bevestigingsmail.
#. De inzending wordt nu verwerkt met de gekoppelde registratieplugin (dus pas ná het
   mede-ondertekenen).

Zonder links in emails
======================

#. De klant navigeert naar het formulier, waar de inlogopties zoals gebruikelijk
   zichtbaar zijn, aangevuld met de "mede-ondertekeneninlogopties".

   .. image:: _assets/cosign_buttons.png
       :width: 100%

#. De klant logt in en vult het formulier in.
#. Bij het "mede-onderteken"-component vult de klant het e-mailadres van de
   ondertekenaar in.
#. Zodra het formulier ingestuurd wordt, worden e-mails verstuurd:

   * de klant krijgt een bevestigingsmail (als deze inschakeld is)
   * de ondertekenaar krijgt een e-mail met het ondertekenverzoek, met instructies om
     het formulier te openen. In de e-mail staat een verificatiecode voor de inzending.

#. De ondertekenaar navigeert naar de startpagina van het formulier en logt in met de
   **Log in om het formulier mede te ondertekenen**-knop.
#. Vervolgens moet de ondertekenaar de verificatiecode uit de e-mail invullen. Bij een
   geldige code ziet de gebruiker een overzicht van de ingevulde gegevens.
#. Indien relevant accepteert de ondertekenaar de verklaring van waarheid
   en/of privacybeleid. Daarna bevestigt die de mede-ondertekening.
#. De klant en de ondertekenaar ontvangen allebei een bevestigingsmail.
#. De inzending wordt nu verwerkt met de gekoppelde registratieplugin (dus pas ná het
   mede-ondertekenen).
