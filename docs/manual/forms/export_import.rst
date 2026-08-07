.. _manual_export_import:

========================
Exporteren en importeren
========================

In Open Formulieren kunt formulieren in zijn geheel exporteren en importeren. Zo
kunt u eenvoudig formulieren delen met anderen of overzetten van een test- naar
productie-omgeving.

Formulieren exporteren
======================

U kunt elk formulier eenvoudig exporteren door onderstaande stappen te volgen:

1. Navigeer naar **Formulieren** > **Formulieren**.
2. Klik op de titel van het gewenste formulier om het formulier te openen.
3. Klik onderaan op de knop **Exporteren**
4. Een ZIP-bestand, met de naam van het *URL-deel* van het formulier, wordt nu
   gedownload op uw computer.

U hoeft het ZIP-bestand niet uit te pakken.

.. note::

    **Technische achtergrond**

    Formulieren worden geëxporteerd als een ZIP-bestand waarin meerdere
    JSON-bestanden zitten. Elk JSON-bestand bevat de configuratie van het
    formulier zelf of een stap binnen het formulier. De JSON-structuur komt
    1-op-1 overeen met de API-specificatie waardoor het export formaat tevens
    open en transparent is.

Formulier exporteer opties
--------------------------

Bij het exporteren van een formulier heb je enkele opties over hoe het
ZIP-bestand wordt gemaakt:

* **Anonimiseer formulierinstellingen**: Indien aangevinkt, dan worden de
  formulierinstellingen automatisch geanonimiseerd. Dit verwijderd alle
  e-mailadressen die zijn configureerd in de E-mail registratie en de interne
  opmerkingen op het formulier. Deze optie is standaard aangevinkt.
* **Formulierinstellingen**: Hiermee kunnen registratie backends,
  betaalprovider, prefill en inlogmethode eenvoudig bij het exporteren
  weggelaten worden. Standaard worden alle instellingen mee geëxporteerd.
* **Aanvullende formulierinstellingen**: Hiermee kunnen aanvullende
  instellingen van het formulier aan het ZIP-bestand toegevoegd worden.

Formulieren importeren
======================

Formulieren die zijn geëxporteerd met Open Formulieren kunnen ook weer
geïmporteerd worden.

1. Navigeer naar **Formulieren** > **Formulieren**.
2. Klik rechtsboven op de knop **Formulier importeren**.
3. Klik op **Bestand kiezen** en selecteer het gewenste ZIP-bestand.
4. Klik op **Importeren**

Als het goed is, is het formulier inclusief alle stappen geïmporteerd. Het
geïmporteerde formulier is standaard niet actief en dus niet direct voor de
buitenwereld toegankelijk.

Formulier importeer opties
--------------------------

Bij het importeren van een formulier heb je enkele opties over hoe het
ZIP-bestand wordt geïmporteerd en hoe het formulier wordt gemaakt:

* **Formulierinstellingen**: Hiermee kunnen registratie backends,
  betaalprovider, prefill en inlogmethode eenvoudig bij het importeren
  weggelaten worden. Standaard worden alle instellingen mee geïmporteerd.
* **Aanvullende formulierinstellingen**: Hiermee kunnen aanvullende
  instellingen uit het ZIP-bestand toegevoegd worden aan het formulier. Bij het
  importeren wordt gekeken of de aanvullende objecten, zoals producten, al in
  de Open Formulieren-omgeving bestaan. Zo ja, worden deze bestaande objecten
  hergebruikt, zo niet worden ze aangemaakt.
* **Hergebruik formulierdefinities**: Hiermee kan aangegeven worden of al
  bestaande herbruikbare formulierdefinities gebruikt moeten worden, of dat
  elke formulierdefinitie opnieuw aangemaakt moet worden.
* **Stijl**: Welk stijl gebruik zal worden voor het formulier.
* **Categorie**: In welke categorie het formulier geplaatst zal worden.

Bijzonderheden
--------------

Als het *URL-deel* van een te importeren formulier zelf al bestaat, dan wordt
het *URL-deel* van het te importeren formulier uniek gemaakt door een reeks van
letters en cijfers er achter te plaatsen. Na het importeren kunt u het
*URL-deel* nakijken en eventueel aanpassen.

Export en import van :ref:`logica <manual_logic>` regels die gebruik maken van
het experimentele bevragen van registraties is niet geïmplementeerd. De
logica-regels zullen wel geëxporteerd en geïmporteerd worden, maar de
servicebevragingconfiguraties niet. Gaat u bij deze regels dus altijd na of de
gebruikte configuraties nog wel daadwerkelijk bestaan!
