.. _manual_form_fields:

===============
Formuliervelden
===============

Alle velden in een formulier zijn van een bepaald type, het veld type.

Algemeen
========

Veel veld typen (ook wel componenten genoemd) hebben soortgelijke opties en 
functies. Hieronder staan de meest voorkomende genoemd, onderverdeeld in de
tabbladen binnen het component.

Basis
-----

* **Label**: Het label bij het veld dat zichtbaar is voor de eindgebruiker.
* **Eigenschapnaam**: De interne naam van het veld. Deze naam wordt gebruikt om
  eenduidig naar dit veld te verwijzen vanuit andere velden of in 
  :ref:`sjablonen <manual_templates>`.
* **Beschrijving**: Een optionele help tekst bij het veld.
* **Weergeven in bevestigingsmail**: Indien aangevinkt, dan wordt dit veld opgenomen in de
  bevestigingsmail naar de eindgebruiker.
* **Verborgen**: Indien aangevinkt, dan is het veld onzichtbaar voor de
  eindgebruiker. Dit kan bijvoorbeeld gebruikt worden om informatie voor in te 
  vullen en door te zetten naar achterliggende registratiesystemen. Beheerders
  kunnen de waarden van onzichtbare velden uiteraard wel zien.

.. _manual_forms_form_fields_variables_usage:

Variabelen
~~~~~~~~~~

U kunt :ref:`variabelen <manual_forms_basics_variables>` gebruiken in het ontwerp van formulieren, 
bijvoorbeeld om een (voor-)ingevulde naam in het label van een ander 
formulierveld weer te geven. Hiervoor is de 
:ref:`sjabloonfunctionaliteit <manual_templates>` beschikbaar.

.. note::

    Alle velden in een formulier zijn als variabele beschikbaar. Daarnaast zijn er ook
    altijd een aantal :ref:`vaste variabelen beschikbaar én u kunt zelf ook variabelen
    definiëren <manual_forms_basics_variables>`.

Stel dat u een formulier hebt met de volgende velden:

* Voornaam partner (met eigenschapnaam ``partnerNaam``)
* Achternaam partner (met eigenschapnaam ``partnerAchternaam``)

Dan kunt u een veld toevoegen met:

* **Eigenschapnaam**: ``partnerGeboortedatum``
* **Label**: ``Geboortedatum {{ partnerNaam }}``

.. image:: _assets/form_field_template_variables.png
    :width: 100%

Wanneer eindgebruiker dan als voornaam "Willy" invult, dan wordt het label voor de
geboortedatum "Geboortedatum Willy". Merk op dat dit niet beschikbaar is in de
formulierdesigner, enkel bij het daadwerkelijk invullen van een formulier.

Deze functionaliteit is beschikbaar op de volgende opties:

* **Label**
* **Standaardwaarde**
* **Beschrijving**
* **Placeholder**
* **Inhoud** bij vrije-tekst

Geavanceerd
-----------

* **This component should Display**: Selecteer ``True`` om het veld te tonen als
  onderstaande conditie geldt. Selecteer ``False`` om het veld juist te 
  verbergen als onderstaande conditie geldt.
* **When the form component**: Selecteer een ander veld dat een specifieke 
  waarde moet hebben om dit veld te tonen of te verbergen.
* **Has the value**: De waarde die het andere veld moet hebben om de conditie te
  laten slagen.

**Voorbeeld**

Stel er zijn 2 velden:

* Een *Radio* ``Stelling`` met als *Eigenschapnaam* ``stelling``, en 3 waarden:
  ``ja``, ``nee`` en ``anders``.
* Een *Text Field* ``Toelichting bij anders``. Dit veld wordt als volgt 
  ingesteld:

  * **This component should Display**: ``True``
  * **When the form component**: ``stelling``
  * **Has the value**: ``anders``

Er is nu een formulier gemaakt waarbij het tekstveld ``Toelichting bij anders``
alleen zichtbaar wordt indien als ``Stelling`` de waarde ``anders`` is gekozen.

.. image:: _assets/form_field_advanced_0.png
    :width: 49%

.. image:: _assets/form_field_advanced_1.png
    :width: 49%


.. _manual_form_fields_validation:

Validatie
---------

* **Verplicht**: Indien aangevinkt dan is dit veld verplicht voor de 
  eindgebruiker.

* **Plugin**: U kunt gebruik maken van een externe plugin om een veld te 
  valideren. De waarde van het veld wordt naar de plugin gestuurd en 
  gevalideerd.

**Foutmeldingen**

Open Formulieren heeft standaardfoutmeldingen bij verschillende typen van
validatiefouten (denk aan "verplicht", "maximale lengte"...). U kunt deze foutmeldingen
per formulierveld gericht instellen per ondersteunde taal.

In de foutmelding kunt refereren naar het formulierveld. Bijvoorbeeld voor een
``required`` veld: "Het veld {{ field }} is verplicht". Op het moment van weergave wordt
``{{ field }}`` vervangen met de naam van het veld.

Registratie
-----------

* **Registration attribute**: Indien u de waarde van dit veld wilt doorzetten
  naar het achterliggende registratie systeem, dan kunt u hier een attribuut
  kiezen dat beschikbaar is in het achterliggende registratie systeem.


Globale configuratieopties
==========================

Stijl van verplichte velden in formulieren
------------------------------------------

Bij het aanmaken van een formulier zijn velden standaard "optioneel" (in tegenstelling
tot "verplicht"), zie :ref:`manual_form_fields_validation`. Standaard worden verplichte
velden weergegeven met een asterisk in de frontend.

U kunt dit standaardgedrag aanpassen. Onder **Admin** > **Configuratie** >
**Algemene configuratie** > *Standaardformulieropties* vindt u:

* **Formulierenvelden zijn standaard 'verplicht'**

  Als dit checkbox is aangevinkt, zijn velden standaard verplicht. Om ze dan optioneel
  te maken, moet u de checkbox 'verplicht' uitvinken.

* **Markeer verplichte velden met een asterisk**

  Als deze checkbox uitgevinkt is, dan hebben verplichte velden geen asterisk meer
  naast het label. Optionele velden hebben dan wel '(optioneel)' naast het label.


Tekstveld
=========

Het *Tekstveld* heeft de meest uitgebreide opties van alle veld typen.

Basis
-----

* **Show Character Count**: Indien aangevinkt, dan wordt een teller getoond aan
  de eindgebruiker met het aantal karakters dat is ingevuld.

Location
--------

* **Straatnaam afleiden**: Indien aangevinkt, dan zal in dit veld automatisch de
  straatnaam worden ingevuld op basis van het ingevulde postcode en huisnummer.
* **Stad afleiden**: Indien aangevinkt, dan zal in dit veld automatisch de
  stad worden ingevuld op basis van het ingevulde postcode en huisnummer.
* **Postcodecomponent**: Selecteer het veld waarin de eindgebruiker de postcode
  zal invoeren. Dit wordt gebruikt voor het ophalen van de straatnaam en stad.
* **Huisnummercomponent**: Selecteer het veld waarin de eindgebruiker het
  huisnummer zal invoeren. Dit wordt gebruikt voor het ophalen van de straatnaam
  en stad.

**Voorbeeld**

Stel er zijn 4 velden:

* Een *Text Field* (of *Postcode Field*) ``Postcode``.
* Een *Text Field* ``Huisnummer``.
* Een *Text Field* ``Straat`` dat als volgt is ingesteld:

  * **Straatnaam afleiden**: *Aangevinkt*
  * **Postcodecomponent**: ``Postcode (postcode)``
  * **Huisnummercomponent**: ``Huisnummer (huisnummer)``

* Een *Text Field* ``Stad`` dat als volgt is ingesteld:

  * **Stad afleiden**: *Aangevinkt*
  * **Postcodecomponent**: ``Postcode (postcode)``
  * **Huisnummercomponent**: ``Huisnummer (huisnummer)``

  Er is nu een formulier gemaakt waarbij de straat en de stad automatisch worden
  ingevuld als de postcode en het huisnummer zijn ingevuld.


Keuzelijst
==========

Met een *Keuzelijst* kunt u lijst van opties aanbieden, deze lijst kan voorgedefinieerd zijn of dynamisch (zie :ref:`Formulier met dynamische opties <example_logic_dynamic_options>`).

Basis
-----

* **Values**: Hier voert u de lijst van beschikbare opties op. De kolom ``Label`` dient
  voor de weergave van de optie, en de kolom ``Value`` bevat de systeemwaarde. Indien u
  dit veld verder verwerkt, dan moet u de systeemwaarde gebruiken voor vergelijkingen.

  .. note:: Het is niet mogelijk om een lege systeemwaarde op te voeren. Indien u een
     lege optie wil aanbieden in combinatie met een niet-lege standaardwaarde, dan
     dient u een hiervoor expliciet een optie op te voeren. Als systeemwaarde kunt u
     bijvoorbeeld ``-`` gebruiken. Als weergave kunt u bijvoorbeeld ``-------`` of
     ``- geen keuze -`` gebruiken.
