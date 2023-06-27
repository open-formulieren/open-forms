.. _example_service_fetch:

==============================================
Formulier met waarden uit externe registraties
==============================================

.. note::

   Dit voorbeeld maakt gebruik van de **experimentele** functionaliteit ``Bevragen
   registraties``, welke onder **Configuratie** > **Algemene configuratie** >
   **Feature flags, test- en ontwikkelinstellingen** in te schakelen is.

In dit voorbeeld maken we een deel-formulier bestaande uit 1 stap, waarbij er een keuzelijst
met product categorieën die opgehaald wordt uit de `dummyjson-service`_, welke
keuze we verder gebruiken om de producten keuzelijst te vullen.

We gaan ervan uit dat u een :ref:`formulier met geavanceerde logica
<example_advanced_logic>` kunt maken.

Formulier maken
===============

#. Maak een formulier aan met de volgende gegevens:

    * **Naam**: Productaanvraag

#. Klik op het tabblad **Stappen en velden**.
#. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe
   formulierdefinitie**.
#. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

    * **Naam**: Productkeuze

#. Sleep een **Keuzelijst** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

    * **Label**: Categorie
    * Scroll naar beneden en selecteer bij **Keuzeopties** ``variabele``
    * Vul bij **Opties-expressie** het volgende in:

    .. code-block:: json

      {
         "var": "catagorieen"
      }

#. Sleep een **Keuzelijst** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

    * **Label**: Product
    * Scroll naar beneden en selecteer bij **Keuzeopties** ``variabele``
    * Vul bij **Opties-expressie** het volgende in:

    .. code-block:: json

      {
         "var": "producten"
      }

#. Klik op de **Variabelen** tab in het formulier menu en vervolgens op de **Gebruikersvariabelen** tab

#. Klik op **Variabele toevoegen**
#. Voer bij **Naam** ``Categorieën`` in en kies bij **Datatype** ``Lijst (array)``
#. Herhaal stap 11 en 12 met als **Naam** ``producten``

#.  Klik op de **Logica** tab in het formulier menu
#.  Klik op **Regel toevoegen**, gevolgd door **Geavanceerd**.
#.  Vul bij **Triggervoorwaarde** bij de JsonLogic 
    ``{"!": [{"var": "categorieen"}]}`` in.

#.  Klik op **Actie Toevoegen** en selecteer

    * dan **haal de waarde op uit een externe registratie**
    * **Categorieën (categorieen)**
    * Klik op **Instellen**

      * Vul bij **Naam** ``Haal categorieën op`` in
      * Selecteer bij **HTTP-method** ``GET``
      * selecteer bij **Service** ``dummyJSON``
      * Vul bij **Pad** ``products/categories`` in
      * Selecteer bij **Soort mappingexpressie** ``jq``
      * Vul bij **Mappingexpressie** ``sort`` in

    * Klik op **Opslaan**

    .. note::

        Omdat het antwoord van de dummyJSON service ongesorteerd is, gebruiken
        we de `jq sort functie`_, zodat de opties in de keuzelijst op alfabet
        komen.

        |fetch_categories|

        Deze actie betekent: Als ``categorieen`` leeg is, bevraag de dummyJSON
        service voor ``products/categories``, sorteer het antwoord en sla deze
        Lijst van strings op in ``categorieen``.

#.  Klik op **Regel toevoegen**, gevolgd door **Geavanceerd**.
#.  Vul bij **Triggervoorwaarde** bij de JsonLogic 
    ``{"!!": [{"var": "categorie"}]}`` in.

#.  Klik op **Actie Toevoegen** en selecteer

    * dan **haal de waarde op uit een externe registratie**
    * **Producten (producten)**
    * Klik op **Instellen**

      * Vul bij **Naam** ``Haal producten in categorie op`` in
      * Selecteer bij **HTTP-method** ``GET``
      * selecteer bij **Service** ``dummyJSON``
      * Vul bij **Pad** ``products/category/{{categorie}}`` in
      * Selecteer bij **Soort mappingexpressie** ``JsonLogic``
      * Vul bij **Mappingexpressie** ``{"map": [
        {"var": "products"},
        {"merge": [ {"var": "id"}, {"var": "title"} ]}
        ]}`` in

    * Klik op **Opslaan**

    .. note::

       |fetch_products|

       Deze actie betekent: Als er een ``categorie`` is gekozen, bevraag de
       dummyJSON service voor ``products/category/{{categorie}}`` met de
       gekozen categorie in het pad, neem van elk product object in het
       ``products`` attribuut van het antwoord, de ``id`` en ``title`` en sla
       de resulterende lijst van lijsten van 2 strings op in ``producten``.

#.  Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U kunt nu het formulier bekijken.

Eventueel kunt u extra acties aan de regels toevoegen, zodat de ``Product``
keuzelijst alleen zichtbaar is wanneer er een categorie gekozen is:

|logic|

.. warning::

   Het bevragen van services kost tijd en kan de formulierlogica vertragen,
   omdat er op antwoorden gewacht moet worden. Probeer door handig gebruik van
   variabelen en triggers, deze bevragingen tot een minimum te beperken.

   ``Bevragen registraties`` is nog experimenteel van aard. Bekende missende of
   beperkte functionaliteiten zijn onder andere:

   * `het "Probeer het uit" tabje <https://github.com/open-formulieren/open-forms/issues/2777>`_
   * `export/import <https://github.com/open-formulieren/open-forms/issues/2683>`_
   * `slimme caching <https://github.com/open-formulieren/open-forms/issues/2688>`_
   * en `meer <https://github.com/open-formulieren/open-forms/labels/topic%3A%20hergebruik%20waarden>`_

   Door de agile aard van de ontwikkeling staan deze issues staan op het moment
   **niet** op een roadmap.
   
   Daarnaast kan de manier van invoegen van formulier data in de bevragingen
   van syntax veranderen. Op dit moment kunt u met de bekende ``{{variable
   sleutel}}`` syntaxis, waarden invoegen in

   * Pad
   * **waarden** van Query-parameters (niet de *sleutels*)
   * **waarden** van Request-headers (niet de *sleutels*)
   * Body

.. |fetch_categories|
   image:: _assets/service_fetch_categories.png
   :alt: screenshot van de servicebevraging "Haal categorieën op"

.. |fetch_products|
   image:: _assets/service_fetch_products_in_category.png
   :alt: screenshot van de servicebevraging "Haal productin in categorie op"

.. |logic| 
   image:: _assets/service_fetch_logic.png
   :alt: screenshot met extra acties "wijzig een attribuut van een veld/component" Productkeuze: Product (product) verborgen "Ja" resp. "Nee"

.. _dummyjson-service: https://dummyjson.com/docs
.. _jq sort functie: https://jqlang.github.io/jq/manual/#sort,sort_by(path_expression)
