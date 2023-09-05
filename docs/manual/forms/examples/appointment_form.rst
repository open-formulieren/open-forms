.. _manual_forms_examples_appointment_form:

=================
Afspraakformulier
=================

In dit voorbeeld beschrijven we u hoe u een formulier kan instellen zodat de gebruikers
een afspraak voor één of meerdere producten kunnen maken met dit formulier.

Open Formulieren ondersteunt afspraken voor één of meerdere producten/diensten en/of
meerdere personen voor een product/dienst. De details zijn echter afhankelijk van de
specifieke afsprakenmodule waarmee u koppelt.

In dit voorbeeld gaan we er van uit dat u een
:ref:`eenvoudig formulier <example_simple_form>` kan maken.

Configuratie
============

U dient een ondersteunde koppeling te hebben om hiervan gebruik te kunnen maken.

* :ref:`Afsprakenmodule configureren <configuration_appointment_index>`

.. note:: Indien u een andere koppeling hebt die we (nog) niet ondersteunen, neem dan
   contact op om de ontwikkeling te bespreken.

Formulier maken
===============

#. Maak een formulier aan met de volgende gegevens:

   * **Naam**: Afspraak demo

#. Op het tabblad **Formuliergegevens** scrollt u naar beneden in de sectie "Instellingen"

#. Vink de optie **Is afspraakformulier?** aan.

#. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

U hoeft geen individuele stappen/velden in te stellen. Producten, locaties, tijdstippen
en de relevante velden voor klantgegevens worden automatisch opgehaald uit de koppeling.

Voorselectie product
====================

Het is mogelijk om URLs naar het afspraakformulier te maken met een voorgeselecteerd
product. U heeft hiervoor nodig:

* de volledige URL van het formulier, bijvoorbeeld
  ``https://example.com/formulieren/afspraak/``. U kunt deze kopiëren uit de
  "Toon formulier" hyperlink in de lijstweergave.
* de systeem-identificatie van het product wat u wenst voor te selecteren, bijvoorbeeld
  ``123``.

Vervolgens bouwt u de voorselectie URL op als volgt:

.. tabs::

    .. group-tab:: Patroon

        .. code-block:: none

            {{url}}?product={{productIdentificatie}}

    .. group-tab:: Concreet voorbeeld

        .. code-block:: none

            https://example.com/formulieren/afspraak/?product=123


.. _manual_forms_examples_appointment_form_preselect_location:

Voorselectie locatie
====================

Indien u meerdere afspraaklocaties hebt en deze wil beperken tot één enkele locatie,
dan kunt u dit op de :ref:`afsprakenconfiguratie <configuration_appointment_index>`
instellen nadat de koppeling technisch ingesteld is.

.. warning:: Let op - dit schakelt effectief alle overige locaties uit!
