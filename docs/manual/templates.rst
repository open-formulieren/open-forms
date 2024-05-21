.. _manual_templates:

=========
Sjablonen
=========

Open Forms ondersteunt sjablonen voor verschillende aspecten. Sjablonen zijn
teksten die aangepaste kunnen worden op basis van het ingevulde formulier.

.. note::
    Voor de ontwikkelaars documentatie, zie :ref:`developers_backend_core_templating`.

Momenteel worden sjablonen gebruikt voor:

* Bevestigingsmail
* Formulier opslaan e-mail
* Bevestigingspagina
* Registratie e-mail

De tekst kan in deze elementen aangepast worden met **variabelen** en
**voorwaardelijke weergave**. De variabelen die beschikbaar zijn, zijn
afhankelijk van het type sjabloon en het formulier.

Stel, we hebben een formulier met daarin onderstaande velden en een gebruiker
heeft voor elk formulierveld een bepaalde *waarde* ingevuld. Technisch heeft
elk veld een *eigenschap*-attribuut. Dit attribuut identificeert elk veld uniek
en dit is ook het attribuut dat we gebruiken als *variabele*.

==========  =============
Variabele   Waarde
==========  =============
leeftijd    19
geslacht    M
voornaam    John
achternaam  Doe
==========  =============


Hoe het werkt
=============

Variabelen
----------

Met behulp van variabelen kunt u de waarden uit formuliervelden toevoegen aan
de sjabloon.

Om dit te doen gebruikt u de naam van de *eigenschap* tussen dubbele accolades:
``{{ <eigenschap> }}``. Hierbij is ``<eigenschap>`` de daadwerkelijk naam van
de eigenschap, bijvoorbeeld: ``{{ leeftijd }}``.

Voorbeeld
~~~~~~~~~

.. tabs::

   .. tab:: Sjabloon

      .. code:: django

         Hallo {{ voornaam }} {{ achternaam }}!

   .. tab:: Weergave

      .. code:: text

         Hallo John Doe!


Voorwaardelijke weergave
------------------------

Met behulp van voorwaardelijke weergave kunt u bepaalde teksten in sjablonen
tonen of verbergen op basis van bepaalde voorwaarden. Dit zijn zogenaamde
**Als** *dit* **dan** *dat*-constructies.

Om dit te doen kunt u ``{% if <eigenschap> %}``, ``{% elif <eigenschap> %}``,
``{% else %}`` en ``{% endif %}`` opnemen in sjablonen. De voorwaarde
(``if <eigenschap>``) wordt geëvalueerd naar waar of onwaar. Indien waar, dan
wordt de tekst tussen twee van de ``{% %}``-instructies weergeven. Een
``if``-instructie moet worden afgesloten met een ``endif``-instructie.

U kunt ``and`` en ``or`` gebruiken om meerdere ``eigenschappen`` te evalueren
en u kunt variabelen vergelijken met een bepaalde waarde door verschillende
operatoren te gebruiken: ``==`` (gelijk aan), ``!=`` (niet gelijk aan), ``>``
(groter dan) of ``<`` (kleiner dan). De laatste twee kunnen alleen met
numerieke waarden.

Als u geen vergelijking maakt, controleert de ``if``-instructie simpelweg of
de waarde van de ``eigenschap`` niet leeg is. Ten slotte kunt u controleren
of een variabele leeg is door ``not`` ervoor te zetten:
``{% if not <eigenschap> %}...``

Het is mogelijk om voorwaarden binnen andere voorwaarden te gebruiken.

Voorbeeld
~~~~~~~~~


.. tabs::

   .. tab:: Sjabloon

      .. code:: django

         Hallo {% if geslacht == 'M' %} Dhr. {% elif geslacht == 'V' %} Mevr. {% else %} Dhr/Mevr. {% endif %} {{ achternaam }}!

      .. code:: django

         {% if leeftijd < 21 and voornaam %} Hallo {{ voornaam }} {% else %} Hallo {{ achternaam }} {% endif %}


   .. tab:: Weergave

      .. code:: text

         Hallo meneer Doe!

      .. code:: text

         Hoi Joe!


.. _`manual_templates_formatting_of_variables`:

Formattering van variabelen
---------------------------

Vaak wilt u :ref:`variabelen <manual_forms_basics_variables>` op een bepaalde manier formatteren.
Dit is mogelijk met behulp van de *sjabloonfilters* die standaard ingebouwd
zijn. Alle beschikbare filters zijn gedocumenteerd op de
`Django defaultfilters reference`_. Het patroon is typisch:
``{{ <variable>|<sjabloonfilter> }}``

Hieronder vindt u een tabel met vaak-voorkomende patronen.

=================================== ================================== ================================================
Expressie                           Voorbeeld waarde                   Toelichting
=================================== ================================== ================================================
``{{ now|date:"l j F Y" }}``        ``dinsdag 23 augustus 2022``       Datum van vandaag, tekstueel
``{{ now|date:"d/m/Y" }}``          ``23/08/2022``                     Datum van vandaag, d/m/y
``{{ now|date:"m" }}``              ``08``                             Huidige maand
``{{ now|date:"d" }}``              ``23``                             Huidige dag
``{{ now|date:"Y" }}``              ``2022``                           Huidig jaar
``{{ now|date:"F" }}``              ``augustus``                       Huidige maandnaam
``{{ now|date:"l" }}``              ``dinsdag``                        Huidige dagnaam
``{{ now|date:"W" }}``              ``34``                             ISO-8601 weeknummer
``{{ now|time:"H:i" }}``            ``09:08``                          Huidig tijstip (uren en minuten)
``{{ now|time:"H:i:s" }}``          ``09:08:42``                       Huidig tijstip (uren, minuten en seconden)
``{{ legeVariabele|default:"-" }}`` ``-``                              Terugvalwaarde indien de variabele "leeg" is
``{{ filesize|filesizeformat }}``   ``117,7 MB``                       Weergave van bytes (nummer) in leesbare vorm
``{{ consent|yesno:"ok,niet ok"}}`` ``niet ok``                        Weergave op basis van ``True``/ ``False`` waarde
``{{ getal|add:"2" }}``             ``5``                              Equivalent van de som ``getal + 2``
``{{ getal|add:"-2" }}``            ``1``                              Verminder de variabele ``getal`` met 2
``{{ getal|floatformat }}``         ``3,1``                            Rond een getal af op één decimaal als er een
                                                                       decimaal gedeelte is
``{{ getal|floatformat }}``         ``3``                              Indien er geen decimaal gedeelte is, toon dan
                                                                       geen decimalen
``{{ getal|floatformat:"2" }}``     ``3,00``                           Rond altijd het getal af op twee decimalen
``{{ getal|floatformat:"-2" }}``    ``3``                              Rond het getal af op twee decimalen als er een
                                                                       decimaal gedeelte is
``{{ getal|floatformat:"2g" }}``    ``3.000,00``                       De ``g`` suffix past groepering toe
``{{ getal|stringformat:"i" }}``    ``2023``                           Geef de waarde (als integer) zonder groepering
                                                                       van duizendtallen
``{{ lijst|join:", " }}``           ``a, b, c``                        Voeg elementen in een lijst van waarden samen,
                                                                       gescheiden door een komma
``{{ variabele|length }}``          ``12``                             Bereken de lengte van een lijst of string
``{{ variabele|lower }}``           ``kleine letters``                 Converteer een tekst naar kleine letters
``{{ variabele|upper }}``           ``HOOFDLETTERS``                   Converteer een tekst naar hoofdletters
``{{ value|timesince }}``           ``1 week, 2 dagen``                Tijd geleden, relatief ten opzichte van "nu"
``{{ value|timesince|yesterday }}`` ``1 dag``                          Tijd geleden, relatief ten opzichte van de
                                                                       variabele ``yesterday``
``{{ value|timeuntil }}``           ``1 week, 2 dagen``                Tijd tot, relatief ten opzichte van "nu"
``{{ value|timeuntil|tomorrow }}``  ``1 dag``                          Tijd tot, relatief ten opzichte van de variabele
                                                                       ``tomorrow``
``{{ variabele|title }}``           ``Een Omgezette Tekst``            Maak alle woorden startend met hoofdletter, de
                                                                       rest worden kleine letters
``{{ variabele|truncatechars:5 }}`` ``Twee…``                          Breek tekst af tot 5 karakters
``{{ variabele|truncatewords:3 }}`` ``Eén twee …``                     Breek tekst af tot 3 woorden
``{{ variabele|urlize }}``          ``<a href="$url">$url</a>``        Maak hyperlinks in de variabele klikbaar
``{{ getal|divisibleby:"3" }}``     ``True``                           ``True``/``False`` indien de variabele wel/niet
                                                                       deelbaar is
``{{ lijst|first }}``               ``Eerste waarde``                  Geef het eerste element in een lijst van waarden
                                                                       terug
=================================== ================================== ================================================

Je kan ook meerdere filters combineren om geavanceerde manipulaties te doen,
bijvoorbeeld:

.. code-block:: django

    {{ today|date:'Y'|add:"-1"|stringformat:"i" }}

In het jaar 2024 produceert dit de output ``2023``:

#. ``today`` is een ``datetime`` met de waarde 29 februari 2024
#. ``today|date:'Y'`` leidt tot enkel het jaar, dus ``2024``
#. ``1`` aftrekken van ``2024`` geeft ``2023``
#. Tot slot wordt ``2023`` als integer weergegeven zodat de output ``2023`` is en niet
   ``2.023`` (dus zonder groepering van duizendtallen)

.. note:: Sjablonen worden in dezelfde taal/localisatie gerenderd als de taal van de inzending.

Template tags
-------------

De volgende template tags kunnen ook worden gebruikt in opmaakcomponenten.

**get_value**

Geeft de mogelijkheid om een waarde uit een sleutel-waarde variabele te halen.
Bijvoorbeeld, als deze variabele in het formulier bestaat:

.. code:: python

   eenVariabele = {"optie 1": "waarde 1", "optie 2": "waarde 2"}

Dan zal de template tag ``get_value`` de waarde ``waarde 1`` teruggeven:

.. code:: django

   {% get_value eenVariabele 'optie 1' %}


Bevestigingsmail
================

De bevestigingsmail is een optionele e-mail die wordt verzonden wanneer een
gebruiker een formulier verstuurd. De bevestigingsmail heeft toegang tot alle
gegevens uit het formulier en de waarden ingevuld door de gebruiker.

Als een formulier een medeondertekenencomponent bevat, dan wordt na het ondertekenen
een bevestigingsmail gestuurd naar de hoofdpersoon die het formulier heeft ingestuurd.
De medeondertekenaar wordt hierbij in de CC opgenomen en ontvangt deze e-mail dus ook.

**Speciale instructies**

Dit zijn aanvullende variabelen en instructies die beschikbaar zijn voor de
sjabloon. Als een variabele niet beschikbaar maar wel aanwezig is in het
sjabloon, dan wordt deze niet getoond.

==================================  ===========================================================================
Variabele                           Beschrijving
==================================  ===========================================================================
``{% confirmation_summary %}``      Kop "Samenvatting" gevolgd door een volledige samenvatting van alle formuliervelden die zijn gemarkeerd om in de e-mail weer te geven.
``{{ form_name }}``                 De naam van het formulier.
``{{ submission_date }}``           De datum waarop het formulier is verzonden.
``{{ public_reference }}``          De openbare referentie van de inzending, bijvoorbeeld het zaaknummer.
``{% appointment_information %}``   Kop "Afspraakinformatie" gevolgd door de afspraakgegevens, zoals product, locatie, datum en tijdstip.
``{% product_information %}``       Zonder kop, geeft dit de tekst weer uit het optionele veld "informatie" van het product dat aan dit formulier is gekoppeld.
``{% payment_information %}``       Kop "Betaalinformatie" gevolgd door een betaallink indien nog niet is betaald en anders de betalingsbevestiging.
``{% cosign_information %}``        Kop "Medeondertekeneninformatie" gevolgd door informatie over de status van medeondertekenen.
==================================  ===========================================================================

.. note::

   De speciale instructie ``{% summary %}`` is verouderd en zal vanaf versie 3.0.0 niet meer beschikbaar zijn.

Voorbeeld
---------

.. tabs::

   .. tab:: Sjabloon (zonder opmaak)

      .. code:: django

         Beste {{ voornaam }} {{ achternaam }},

         U heeft via de website het formulier "{{ form_name }}" verzonden op {{ submission_date }}.

         Uw referentienummer is: {{ public_reference }}

         {% cosign_information %}

         Let u alstublieft op het volgende:

         {% product_information %}

         {% confirmation_summary %}
         {% appointment_information %}
         {% payment_information %}

         Met vriendelijke groet,

         Open Formulieren

   .. tab:: Weergave (impressie)

      .. code:: markdown

         Beste John Doe,

         U heeft via de website het formulier "Voorbeeld" verzonden op 17 januari 2022.

         Uw referentienummer is: OF-123456

         **Medeondertekenen informatie**

         Dit formulier wordt pas in behandeling genomen na medeondertekening. Er is een verzoek verzonden naar cosigner@test.nl.

         Let u alstublieft op het volgende:

         Vergeet uw paspoort niet mee te nemen.

         **Samenvatting**

         - Voornaam: John
         - Achternaam: Doe

         **Afspraak informatie**

         *Product(en)*
         - Product 1

         *Locatie*
         Straat 1
         1234 AB Stad

         *Datum en tijd*
         21 januari 2022, 12:00 - 12:15

         *Opmerkingen*
         Geen opmerkingen

         Als u uw afspraak wilt annuleren of wijzigen kunt u dat hieronder doen.
         Afspraak annuleren: https://example.com/...
         Afspraak wijzigen: https://example.com/...

         **Betaalinformatie**

         Betaling van EUR 10,00 vereist. U kunt het bedrag betalen door op onderstaande link te klikken.
         Ga naar de betalingspagina: https://example.com/...

         Met vriendelijke groet,

         Open Formulieren


Formulier opslaan e-mail
========================

**Speciale instructies**

Dit zijn aanvullende variabelen en instructies die beschikbaar zijn voor de
sjabloon. Als een variabele niet beschikbaar maar wel aanwezig is in het
sjabloon, dan wordt deze niet getoond.

==================================  ===========================================================================
Variabele                           Beschrijving
==================================  ===========================================================================
``{{ form_name }}``                 De naam van het formulier.
``{{ save_date }}``                 De datum waarop het formulier is opgeslagen.
``{{ expiration_date }}``           De datum waarop het formulier zal vervallen.
``{{ continue_url }}``              De URL om het formulier te hervatten. Deze URL begint al met ``https://``,
                                    dus u kunt 'Nee' kiezen wanneer de pop-up in de editor vraagt om dit toe te
                                    voegen.
==================================  ===========================================================================


Bevestigingspagina
==================

De bevestigingspagina is de pagina die wordt weergegeven nadat het formulier is
verstuurd. De bevestigingspagina heeft toegang tot alle gegevens uit het
formulier en de waarden ingevuld door de gebruiker.

**Speciale instructies**

Dit zijn aanvullende variabelen en instructies die beschikbaar zijn voor de
sjabloon. Als een variabele niet beschikbaar maar wel aanwezig is in het
sjabloon, dan wordt deze niet getoond.

==================================  ===========================================================================
Variabele                           Beschrijving
==================================  ===========================================================================
``{{ public_reference }}``          De openbare referentie van de inzending, bijvoorbeeld het zaaknummer.
``{% product_information %}``       Geeft de tekst weer uit het optionele veld "informatie" van het product dat aan dit formulier is gekoppeld.
==================================  ===========================================================================


Voorbeeld
---------

.. tabs::

   .. tab:: Sjabloon (zonder opmaak)

      .. code:: django

         Bedankt voor uw inzending.

         {% product_information %}

   .. tab:: Weergave (impressie)

      .. code:: markdown

         Bedankt voor uw inzending.

         **Productinformatie**

         Neem alstublieft uw afspraakbevestiging mee.

.. _Django defaultfilters reference: https://docs.djangoproject.com/en/4.2/ref/templates/builtins/#built-in-filter-reference


Registratie e-mail
==================

De registratie-e-mail is een optionele e-mail die wordt verzonden wanneer een formulier is geconfigureerd om de
'e-mailregistratie-backend' te gebruiken. De registratie-e-mail heeft toegang tot alle gegevens uit het formulier en
de waarden ingevuld door de gebruiker.

**Speciale instructies**

Dit zijn aanvullende variabelen en instructies die beschikbaar zijn voor het
sjabloon. Als een variabele niet beschikbaar maar wel aanwezig is in het
sjabloon, dan wordt deze niet getoond.

==================================  ===========================================================================
Variabele                           Beschrijving
==================================  ===========================================================================
``{{ form_name }}``                 De naam van het formulier.
``{{ completed_on }}``              Het moment (datumtijd) waarop het formulier werd ingezonden.
``{{ public_reference }}``          De publieke referentie van de inzending.
``{{ payment_received }}``          Indicatie of de gebruiker wel of niet heeft betaald.
``{{ payment_order_id }}``          De referentie van de betaling.
``{{ submission_language }}``       De taal van het formulier die werd ingezonden, bijvoorbeeld 'nl'.
``{{ co_signer }}``                 De voorletters, achternaam en ID (bijvoorbeeld het BSN) van de persoon die het formulier heeft mede-ondertekend.
``{% registration_summary %}``      Kop "Samenvatting" gevolgd door een volledige samenvatting van alle formuliervelden en gebruikersvariabelen.
==================================  ===========================================================================

Voorbeeld
---------

.. tabs::

   .. tab:: Sjabloon (zonder opmaak)

      .. code:: django

        {% if payment_received %}

        Betaling ontvangen voor {{ form_name }} (verzonden op {{ completed_on }})
        Betalings-order ID: {{ payment_order_id }}

        {% else %}

        Inzendingdetails van {{ form_name }} (verzonden op {{ completed_on }})

        {% endif %}

        Onze referentie: {{ public_reference }}
        Inzendingstaal: {{ submission_language }}

        {% registration_summary %}

        {% if co_signer %}
        Mede-ondertekend door: {{ co_signer }}
        {% endif %}

   .. tab:: Weergave (impressie)

      .. code:: markdown

         Inzendingdetails van Aanvraag stadspas (verzonden op 10:50:25 29-03-2023)

         Onze referentie: OF-H7S6BE
         Inzendingstaal: Nederlands

         **Samenvatting**

         **Uw gegevens**

         - Voornaam: John
         - Achternaam: Doe
         - Postcode: 1111 AA
         - Huisnummer: 1

         **Uw Situatie**

         - Heeft u een uitkering: Nee
         - Heeft u een werkgever: Ja

         **Variabelen**

         - nettoInkomen: 490,0
         - totaalSchuld: 500,0


         Mede-ondertekend door: N. Doe (BSN: 123456789)

E-mail mede-ondertekenverzoek
=============================

De mede-ondertekenverzoek-e-mail wordt verstuurd naar de persoon die aangeduid is als
mede-ondertekenaar als er een mede-ondertekencomponent aan het formulier toegevoegd is.

Deze e-mail bevat de instructies om de inzending te ondertekenen.

**Variabelen**

Enkel de volgende variabelen zijn beschikbaar in dit sjabloon. Geen van deze variabelen
zijn verplicht - je kan bijvoorbeeld instructies opnemen dat de persoon die het
formulier ingevuld heeft de relevante informatie handmatig zal doorgeven.

==================================  ===========================================================================
Variabele                           Beschrijving
==================================  ===========================================================================
``{{ form_name }}``                 De naam van het formulier.
``{{ form_url }}``                  De directe link naar het formulier.
``{{ code }}``                      De code om de inzending mee op te halen.
==================================  ===========================================================================

Voorbeeld
---------

.. tabs::

   .. tab:: Sjabloon (zonder opmaak)

      .. code:: django

         <p>Dit is een verzoek om het formulier "{{ form_name }}" mede te ondertekenen.</p>

         <p>
           Gelieve het formulier te openen met de volgende link:
           <a href="{{ form_url }}">{{ form_url }}</a>.
         </p>

         <p>
           Daarna word je doorgestuurd naar een pagina waar je moet inloggen. Nadat je
           bent ingelogd, haal je het formulier op met de volgende code:
           <br>
           <br>
           <strong>{{ code }}</strong>
         </p>


   .. tab:: Weergave (impressie)

      .. code:: html

         <p>Dit is een verzoek om het formulier "Voorbeeld" mede te ondertekenen.</p>

         <p>
           Gelieve het formulier te openen met de volgende link:
           <a href="https://example.com/voorbeeld-formulier">https://example.com/voorbeeld-formulier</a>.
         </p>

         <p>
           Daarna word je doorgestuurd naar een pagina waar je moet inloggen. Nadat je
           bent ingelogd, haal je het formulier op met de volgende code:
           <br>
           <br>
           <strong>OF-123456</strong>
         </p>

.. _objecten_api_registratie:

Objecten API registratie
========================

.. note:: We adviseren om gebruik te maken van de :ref:`manual_registration_objects_api_variables` in plaats van sjablonen.

De Objecten API-registratiebackend maakt een object aan in de geconfigureerde Objecten API met de gegevens van een
inzending. Een voorbeeld van de JSON die naar de Objecten API wordt gestuurd:

.. code:: json

   {
     "type": "https://objecttype-example.nl/api/v2/objecttype/123",
     "record": {
         "typeVersion": 1,
         "data": {},
         "startAt": "2023-01-01"
     }
   }


De structuur van het veld ``data`` is per formulier instelbaar met een sjabloon. De Objecten API-registratie heeft toegang tot
alle gegevens uit het formulier en de waarden ingevuld door de gebruiker.

.. note :: U bent waarschijnlijk gewend om in andere sjablonen een variabele direct in het sjabloon te gebruiken, zoals
   ``{{ voornaam }}``. Echter, in de sjablonen voor de Objecten API dient u deze als ``variables.<variabele>`` te refereren,
   bijvoorbeeld ``{{ variables.voornaam }}``. Dit zal in de toekomst voor alle sjablonen gelden.

.. seealso ::

   See :ref:`example_form_with_geometry` for a more detailed example.

Voor formulieren die een betaling vereisen, is het ook mogelijk om informatie over de betaling toe te voegen.
Als de gebruiker betaalt, kan de status van de betaling in de Object API bijgewerkt worden. Hier ook is de structuur van het
``record`` veld per formulier instelbaar met een sjabloon.
In dit sjabloon kunnen alleen de inzendingsvariabelen (``variables.<naam van variabele>``) en de ``payment`` variabele
(zie tabel hieronder) gebruikt worden.

.. note::

   De ``payment.amount`` in een JSON sjabloon geeft een ``number``. Het objecttype schema zou de nauwkeurigheid van
   het ``amount`` veld moeten vastleggen door bijvoorbeeld ``type: number, multipleOf: 0.01`` te specificeren.

**Speciale instructies**

Dit zijn aanvullende variabelen en instructies die beschikbaar zijn voor het
sjabloon. Als een variabele niet beschikbaar maar wel aanwezig is in het
sjabloon, dan wordt deze niet getoond.

=====================================  ===========================================================================
Variabele                              Beschrijving
=====================================  ===========================================================================
``{{ productaanvraag_type }}``         Het productaanvraag type.
``{{ submission.public_reference }}``  De publieke referentie van de inzending.
``{{ submission.kenmerk }}``           Het interne ID van de inzending (UUID).
``{{ submission.language_code }}``     De taal waarin de gebruiker het formulier invulde, bijvoorbeeld 'nl' of 'en'.
``{{ submission.pdf_url }}``           De URL van het inzendingsrapport (in PDF formaat) in de documenten API.
``{{ submission.csv_url }}``           De URL van het inzendingsrapport (in CSV formaat) in de documenten API. Dit document is mogelijk niet aangemaakt
``{% json_summary %}``                 JSON met ``"<variabele-eigenschapsnaam>": "<waarde>"`` van alle formuliervelden.
``{% uploaded_attachment_urls %}``     Een lijst met de URLs van documenten toegevoegd door de inzender. De URLs verwijzen naar het geregistreerde document in de Documenten API.
``{% as_geo_json variables.map %}``    Sluit de gerefereerde variabele (`variables.map`) in als JSON.
``{{ payment.completed }}``            Indicatie of de betaling voltooid is.
``{{ payment.amount }}``               Bedrag dat betaald moet worden.
``{{ payment.public_order_ids }}``     Lijst van bestelling IDs die naar de externe betaalprovider meegestuurd zijn.
``{{ cosign_data.date }}``             De datum waarop de inzending mede is ondertekend.
``{{ cosign_data.bsn }}``              Het BSN van de medeondertekenaar, indien beschikbaar.
``{{ cosign_data.kvk }}``              Het KvK van de medeondertekenaar, indien beschikbaar.
``{{ cosign_data.pseudo }}``           Het pseudo van de medeondertekenaar, indien beschikbaar.
=====================================  ===========================================================================


Voorbeeld
---------

.. tabs::

   .. tab:: Sjabloon (zonder opmaak)

      .. code:: django

         {
           "form_data": {% json_summary %},
           "type": "{{ productaanvraag_type }}",
           "bsn": "{{ variables.auth_bsn }}",
           "pdf_url": "{{ submission.pdf_url }}",
           "attachments": {% uploaded_attachment_urls %},
           "submission_id": "{{ submission.kenmerk }}",
           "language_code": "{{ submission.language_code }}",
           "public_reference": "{{ submission.public_reference }}",
           {% if cosign_data %}
           "cosign_date": "{{ cosign_data.date.isoformat }}",
           "cosign_bsn": "{{ cosign_data.bsn }}"
           {% endif %}
         }

   .. tab:: Resultaat

      .. code:: json

         {
           "form_data": {
              "voorNaam": "Jane",
              "achterNaam": "Doe"
           },
           "type": "terugbelnotitie",
           "bsn": "123456782",
           "pdf_url": "http://some-url.nl/to/pdf/report",
           "attachments": ["http://some-url.nl/to/attachment1", "http://some-url.nl/to/attachment2"],
           "submission_id": "c305a56f-c56c-49bc-9d94-3e301d0b8bf8",
           "language_code": "nl",
           "public_reference": "OF-12345",
           "cosign_date": "2024-01-01T12:00:00.037672+00:00",
           "cosign_bsn": "123456783"
         }
