.. _manual_forms_translations:

=============
Meertaligheid
=============

Introductie
===========

Open Formulieren biedt de mogelijkheid om formulieren aan te bieden in meerdere talen,
waarbij de formulierbouwer praktisch alle teksten per ondersteunde taal kan instellen.
Deze handleiding beschrijft hoe u dat doet.

.. _manual_forms_translations_globals:

Globale configuratievertalingen
===============================

Allereerst is er een aantal globaal gebruikte teksten waarvan de vertalingen ingevoerd
dienen te worden. Navigeer hiervoor naar **Configuratie > Algemene configuratie**.

Op deze pagina vindt u de vertaalbare velden - deze hebben achtervoegsels zoals
**[nl]** en **[en]**. U voert hier per taal de gewenste tekst op.

    - **Inzendingen > Bevestigingspagina tekst**
    - **Bevestigingse-mail > Onderwerp**
    - **Bevestigingse-mail > Inhoud**
    - **Sjabloon "pauzeer"-email > Onderwerp**
    - **Sjabloon "pauzeer"-email > Inhoud**
    - **Knop labels > Formulier starten-label**
    - **Knop labels > "terug naar formulier"-tekst**
    - **Knop labels > Stap wijzigen-label**
    - **Knop labels > Formulier verzenden-label**
    - **Knop labels > "vorige stap"-tekst**
    - **Knop labels > Opslaan-label**
    - **Knop labels > Volgende stap-label**
    - **Privacy > Privacybeleid label**

    .. image:: _assets/translations_global_config.png
        :width: 100%

Deze globale configuratie is een éénmalige actie, u hoeft dit niet voor elk formulier
uit te voeren.

Formuliervertalingen
====================

Formuliergegevens
-----------------

Vervolgens kunt u de formulierspecifieke vertalingen inrichten. Dit doet u door naar het
gewenste formulier te navigeren via **Formulieren > Formulieren** en klik dan in de
lijst het relevante formulier aan.

Op de "Formulier"-tab kunt u de formuliergegevens zoals naam en toelichtingssjabloon
per taal invoeren. Wissel tussen talen met de tabjes boven de velden.

    .. image:: _assets/translations_form_details.png
        :width: 100%

Stappen en velden
-----------------

Bij de stapgegevens beheert u vertalingen van de formulierinhoud. Gebruik opnieuw de
tabjes om per taal de metagegevens voor elke stap aan te passen, zoals de naam van een
formulierstap. Voor een aantal elementen (zoals de knopteksten) kunt u hier, indien
gewenst, afwijken van de
:ref:`globale configuratievertalingen <manual_forms_translations_globals>`.

    .. image:: _assets/translations_formstep.png
        :width: 100%

De vertalingen voor de velden van het formulier worden ingevoerd per veld door te
klikken op het tandwiel-icoontje voor dat veld. Vervolgens klikt u in de pop-up op de
tab **Vertalingen**. De tabel toont automatisch alle vertaalbare teksten die in de
veldconfiguratie voorkomen. Mogelijk zijn een aantal vertalingen al vooringevuld omdat
dezelfde tekst al in een ander formulier voorkomt.

U kunt in de vertalingen ook :ref:`variabelen <manual_forms_form_fields_variables_usage>`
gebruiken - deze worden dan dynamisch toegepast tijdens het invullen van het formulier.

    .. image:: _assets/translations_formio.png
        :width: 100%

.. note:: Vertalingen worden hergebruikt per stap, dus als twee velden hetzelfde label
   hebben, zullen ze ook dezelfde vertaling krijgen. U kunt dit voorkomen door
   "placeholders" te gebruiken - gebruik bijvoorbeeld **_veld1_label** als label en voer
   dan voor alle talen de echte tekst op in de vertalingen-tab.

    .. image:: _assets/translations_formio_placeholders.png
        :width: 100%

Bevestiging
-----------

Op de bevestigingstab zijn er nog een aantal vertaalbare velden. Deze werken op dezelfde
manier als de formulierdetailsvelden.

    .. image:: _assets/translations_submission.png
        :width: 100%

Knopteksten
-----------

Ook de knopteksten kunnen vertaald worden. Indien deze niet ingevuld zijn, worden de standaardvertalingen uit de algemene configuratie gebruikt:

    .. image:: _assets/translations_button_literals.png
        :width: 100%


Meertaligheid activeren
=======================

Nu alle vertalingen ingevoerd zijn, kan meertaligheid op het formulier geactiveerd worden.
Om dit te doen dient de optie **Vertalingen ingeschakeld** onder de **Formulier**
tab aangevinkt te worden. Zodra dit ingeschakeld is, zullen gebruikers in het formulier
een keuzemenu hebben om hun voorkeurstaal te activeren.
