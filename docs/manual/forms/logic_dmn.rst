.. _manual_logic_dmn:

====================
Beslistabellen (DMN)
====================

Open Formulieren heeft een module om beslistabellen/beslissingen te evalueren. Deze
dient :ref:`geconfigureerd <configuration_dmn_index>` te zijn voor je hier gebruik van
kan maken.

.. seealso:: Zie ook het voorbeeldformulier :ref:`examples_camunda`.

Wat zijn beslistabellen?
========================

In beslistabellen kan je regels vastleggen - op basis van een aantal inputs en deze
regels volgt hier een (berekend) resultaat uit. Deze tabellen worden door een
*DMN-engine* uitgevoerd om het resultaat te bepalen. Beslistabellen zijn doorgaans
een overzichtelijke, gecentraliseerde manier om regels (zoals wetgeving) te toetsen,
en zijn vaak een goed alternatief voor complexe JsonLogic-expressies.

Configuratie
============

DMN-acties moeten geconfigureerd worden.

**Algemene instellingen**

* Pluginkeuze
* Beslisdefinitie/tabel om te evalueren
* Eventuele versie van de beslissing - indien niet opgegeven, dan wordt de meest recente
  versie gebruikt.

**In- en uitvoerparameters**

Bij de invoerparameters worden de waardes van formuliervariabelen ingestuurd als input
voor de geselecteerde beslistabel. Formuliervariabelen en beslistabelvariabelen kunnen
hierbij verschillende namen hebben.

Op deze manier stuur je de gebruikersinvoer tijdens het invullen van het formulier naar
de beslistabel. Je kan ook statische variabelen of zelf-gedefinieerde variabelen koppelen.

.. note::

   Let op dat je het juiste datatype selecteert - als de tabel een getal verwacht,
   dan mag je geen tekstuele waarden/variabelen koppelen.

   Als je een letterlijke booleanwaarde (``true``/``false``) nodig hebt, let er dan op
   dat je als formulierveld een selectievakje gebruikt - radio en keuzemenu-opties
   worden namelijk als tekstuele waarde geïnterpreteerd.

Uitvoerparameters schrijven het resultaat van de beslistabel terug naar
formuliervariabelen. Je kan hiermee veldwaarden en zelf-gedefinieerde variabelen
(over)schrijven. Vervolgens kan je deze variabelen ook weer gebruiken in andere
logicaregels.
