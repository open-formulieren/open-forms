.. _manual_forms_translations:

=============
Meertaligheid
=============

Introductie
===========

.. todo:: Not sure if Vertalingen ingeschakeld is the correct literal, as it isn't translated yet

Open Formulieren biedt de mogelijkheid om formulieren aan te bieden in meerdere talen (momenteel alleen Nederlands en Engels).
Om dit mogelijk te maken is het van belang dat de Nederlandse termen in het formulier vertaald worden naar de gekozen taal
en in deze handleiding wordt uitgelegd hoe deze vertalingen in te voeren zijn via de beheerinterface.

Globale configuratievertalingen
===============================

.. todo:: Several labels mentioned in the enumeration not yet translated

Allereerst zijn er een aantal globaal gebruikte woorden en zinnen waarvan de vertalingen ingevoerd moeten worden,
dit kan door naar **Configuratie > Algemene configuratie** te navigeren. Op die pagina zijn een aantal velden te zien
met een **[nl]** en een **[en]** versie. Op deze manier is het mogelijk om voor de volgende velden vertalingen in te voeren:

    - **Inzendingen > Bevestigingspagina tekst**
    - **Bevestigingse-mail > Onderwerp**
    - **Bevestigingse-mail > Inhoud**
    - **Sjabloon "pauzeer"-email > Onderwerp**
    - **Sjabloon "pauzeer"-email > Inhoud**
    - **Knop labels > Formulier starten-label**
    - **Knop labels > Back to form text**
    - **Knop labels > Stap wijzigen-label**
    - **Knop labels > Formulier verzenden-label**
    - **Knop labels > Previous step text**
    - **Knop labels > Opslaan-label**
    - **Knop labels > Volgende stap-label**
    - **Privacy > Privacybeleid label**

    .. image:: _assets/translations_global_config.png
        :width: 100%

Formuliervertalingen
====================

Formulierdetails
----------------

De volgende stap is om formulierspecifieke vertalingen in te voeren, dit gebeurt in de beheerinterface van het desbetreffende formulier.

Allereerst moeten de vertalingen voor de naam en het toelichtingssjabloon ingevoerd worden. Het wisselen tussen talen gebeurt d.m.v.
de tabjes boven de velden.

    .. image:: _assets/translations_form_details.png
        :width: 100%

Stappen en velden
-----------------

Bij de stapgegevens zijn er een aantal vertalingen die ingevoerd moeten worden, zoals te zien hieronder. Wisselen tussen talen
gebeurt wederom met de tabjes. Indien deze niet ingevuld zijn, worden de standaardvertalingen uit de algemene configuratie gebruikt.

    .. image:: _assets/translations_formstep.png
        :width: 100%

.. todo:: UI in these images might be subject to change, in the future they will probably be prefilled

De vertalingen voor de velden van het formulier worden ingevoerd per veld door te klikken op het tandwiel-icoontje
van het veld. Vervolgens kunnen vertalingen ingevoerd worden bij de tab **Vertalingen**:

    .. image:: _assets/translations_formio.png
        :width: 100%

.. note:: Vertalingen worden hergebruikt per stap, dus als twee velden hetzelfde label hebben, zullen ze ook dezelfde vertaling krijgen.
    Dit kan voorkomen worden door placeholders te gebruiken, door bijv. **_veld1_label** als label in te voeren voor een veld
    en bij de vertalingen deze placeholder te vertalen voor elke taal:

    .. image:: _assets/translations_formio_placeholders.png
        :width: 100%

.. warning::

    In de beheerinterface voor Formulierdefinities is het op dit moment niet mogelijk om vertalingen van velden in te zien.
    Het is daarom raadzaam om hier de Formulieren beheerinterface voor te gebruiken.

Bevestiging
-----------

Op de bevestigingstab zijn er nog een aantal zaken waarvan de vertalingen ingevoerd moeten worden, dit gebeurt op dezelfde manier als bij de formulierdetails:

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
Om dit te doen dient de optie **Vertalingen ingeschakeld** onder de **Formulier** tab aangevinkt te worden.
Zodra dit ingeschakeld is, zullen gebruikers in het formulier een keuzemenu hebben, waarin ze uit de ondersteunde talen kunnen kiezen.
