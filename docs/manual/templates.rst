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
``{{ now|time:"H:i" }}``            ``09:08``                          Huidig tijstip (uren en minuten)
``{{ now|time:"H:i:s" }}``          ``09:08:42``                       Huidig tijstip (uren, minuten en seconden)
``{{ now|date:"W" }}``              ``34``                             ISO-8601 weeknummer
``{{ legeVariabele|default:"-" }}`` ``-``                              Terugvalwaarde indien de variabele "leeg" is
``{{ filesize|filesizeformat }}``   ``117,7 MB``                       Weergave van bytes (nummer) in leesbare vorm
``{{ consent|yesno:"ok,niet ok"}}`` ``niet ok``                        Weergave op basis van ``True``/ ``False`` waarde
=================================== ================================== ================================================

.. note:: Op dit moment krijgt u altijd de Nederlandse vertalingen/lokalisatie.
   Er is nog geen ondersteuning voor andere talen.


Bevestigingsmail
================

De bevestigingsmail is een optionele e-mail die wordt verzonden wanneer een
gebruiker een formulier verstuurd. De bevestigingsmail heeft toegang tot alle
gegevens uit het formulier en de waarden ingevuld door de gebruiker.

**Speciale instructies**

Dit zijn aanvullende variabelen en instructies die beschikbaar zijn voor de
sjabloon. Als een variabele niet beschikbaar maar wel aanwezig is in het
sjabloon, dan wordt deze niet getoond.

==================================  ===========================================================================
Variabele                           Beschrijving
==================================  ===========================================================================
``{% summary %}``                   Kop "Samenvatting" gevolgd door een volledige samenvatting van alle formuliervelden die zijn gemarkeerd om in de e-mail weer te geven.
``{{ form_name }}``                 De naam van het formulier.
``{{ submission_date }}``           De datum waarop het formulier is verzonden.
``{{ public_reference }}``          De openbare referentie van de inzending, bijvoorbeeld het zaaknummer.
``{% appointment_information %}``   Kop "Afspraakinformatie" gevolgd door de afspraakgegevens, zoals product, locatie, datum en tijdstip.
``{% product_information %}``       Zonder kop, geeft dit de tekst weer uit het optionele veld "informatie" van het product dat aan dit formulier is gekoppeld.
``{% payment_information %}``       Kop "Betaalinformatie" gevolgd door een betaallink indien nog niet is betaald en anders de betalingsbevestiging.
==================================  ===========================================================================

Voorbeeld
---------

.. tabs::

   .. tab:: Sjabloon (zonder opmaak)

      .. code:: django

         Beste {{ voornaam }} {{ achternaam }},

         U heeft via de website het formulier "{{ form_name }}" verzonden op {{ submission_date }}.

         Uw referentienummer is: {{ public_reference }}

         Let u alstublieft op het volgende:

         {% product_information %}

         {% summary %}
         {% appointment_information %}
         {% payment_information %}

         Met vriendelijke groet,

         Open Formulieren

   .. tab:: Weergave (impressie)

      .. code:: markdown

         Beste John Doe,

         U heeft via de website het formulier "Voorbeeld" verzonden op 17 januari 2022.

         Uw referentienummer is: OF-123456

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
``{{ continue_url }}``              De URL om het formulier te hervatten.
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

.. _Django defaultfilters reference: https://docs.djangoproject.com/en/3.2/ref/templates/builtins/#built-in-filter-reference


Registratie
===========

De registratie email is een optionele e-mail die wordt verzonden wanneer een formulier is geconfigureerd om de
'registratie backend' te gebruiken. De registratie email heeft toegang tot alle
gegevens uit het formulier en de waarden ingevuld door de gebruiker.

**Speciale instructies**

Dit zijn aanvullende variabelen en instructies die beschikbaar zijn voor het
sjabloon. Als een variabele niet beschikbaar maar wel aanwezig is in het
sjabloon, dan wordt deze niet getoond.

==================================  ===========================================================================
Variabele                           Beschrijving
==================================  ===========================================================================
``{{ form_name }}``                 De naam van het formulier.
``{{ completed_on }}``              De tijdstip waarop het formulier werd ingezonden.
``{{ public_reference }}``          De openbare referentie van de inzending.
``{{ payment_received }}``          Indicatie of de gebruiker wel of niet heeft betaald.
``{{ payment_order_id }}``          De referentie van de betaling.
``{{ submission_language }}``       De taal van het formulier die werd ingezonden.
``{{ co_signer }}``                 De voorletters en de achternaam van de persoon die het formulier heeft mede-ondertekend.
``{% data_summary %}``              Kop "Samenvatting" gevolgd door een volledige samenvatting van alle formuliervelden en gebruikersvariabelen.
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

        {% data_summary %}

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


         Mede-ondertekend door: N. Doe
