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

Bijzonderheden
--------------

Als een formulier wordt geïmporteerd en het bevat een stap waarvan het 
*URL-deel* overeenkomt met een bestaande stap, dan controleert het import proces
of de te importeren stap **exact hetzelfde** is als de bestaande stap. Als dat 
zo is, dan wordt de bestaande stap gebruikt voor het geïmporteerde formulier. Er
wordt dan geen nieuwe stap aangemaakt.

Als de stap **niet exact hetzelfde** is, dan wordt er een nieuwe stap aangemaakt
en wordt het *URL-deel* van de stap gewijzigd. Bijvoorbeeld van 
``persoonsgegevens`` naar ``persoonsgegevens-2``. U krijgt hier altijd een 
melding van.

Als het *URL-deel* van een te importeren formulier zelf al bestaat, dan kan het 
formulier niet worden geimporteerd. U kunt dan het *URL-deel* van het 
conflicterende formulier zelf aanpassen en het nogmaals proberen.
