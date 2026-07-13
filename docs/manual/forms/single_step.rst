.. _manual_single_step:

===========
Enkele stap
===========

Open Formulieren kent drie soorten formulieren: *standaard*, *afspraak* en *enkele stap*.

.. versionadded:: 4.0

   De éénstapsformulieren zijn nieuw sinds Open Formulieren 4.0.

Formulieren die slechts uit één stap bestaan zijn geoptimaliseerd voor extreem
laagdrempelige formulieren waarbij gebruikers niet dienen in te loggen en gelijk het
formulier kunnen beginnen invullen - zonder startpagina dus. Bijvoorbeeld een
contactformulier wat ingesloten wordt in de publieke website op productpagina's.

Dit type formulier kan ingesteld worden door bij formuliertype "enkele stap" te
selecteren.

Logica
======

Formulierlogica is beperkt beschikbaar - je kan enkel logica instellen die op het eind
van de inzending uitgevoerd wordt, voornamelijk gericht op het juist afhandelen van
de registratie. Enkel de volgende acties zijn beschikbaar:

1. Zet registratieplugin voor de inzending
2. Zet de waarde van een variabele/component
3. DMN evalueren

.. note:: Voor éénstapsformulieren wordt de logica altijd in de backend aan het eind van
   de inzending uitgevoerd.

.. warning:: Voor het zetten van de waarde van een variabele en evalueren van DMN kan je
   enkel gebruik maken van **gebruikersvariabelen**.

Zie :ref:`example_single_step_form` voor een volledig voorbeeld.
