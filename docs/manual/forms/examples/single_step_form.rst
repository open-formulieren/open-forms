.. _example_single_step_form:

==============================
Eénstapsformulier (met logica)
==============================

Formulieren die slechts uit één stap bestaan zijn geoptimaliseerd voor extreem
laagdrempelige formulieren, bijvoorbeeld om te voldoen aan WMEBV-eisen om makkelijk
digitaal contact op te nemen.

.. tip:: Formulierlogica bij éénstapsformulieren wordt enkel aan het eind van de
   inzending uitgevoerd, wanneer de gebruiker de inzending afgerond heeft. Er is dus
   geen logica mogelijk *tijdens* het invullen.

Formulier maken
===============

#. Maak een formulier aan met de volgende gegevens:

  * **Naam**: Demo éénstapsformulier
  * **Type**: Enkele stap
  
  .. image:: _assets/form-type.png

#. Klik op het tabblad **Stappen en velden** en voeg een nieuwe (de enige) stap toe.
#. Sleep een component (bijvoorbeeld *e-mail*) in de stap. Het maakt niet uit wat voor
   component je kiest voor dit voorbeeld.
#. Klik op het tabblad **Variabelen**. Klik hierbinnen op het tabblad
   **Gebruikersvariabelen**.
#. Voeg een variabele toe door op **Variabele toevoegen** link te klikken, en voer in:

   * **Naam**: *Afdeling*
   * **Datatype**: laat de standaardwaarde (tekst) staan

#. Klik op het tabblad **Logica** en voeg een geavanceerde logicaregel toe:

   .. image:: _assets/single_step_logic.png

   .. note:: Deze logicaregel berekent waar de inzending heen moet. Op basis van de vaste
      variabele ``form_url`` kan afgeleid worden vanaf welke pagina de inzending komt,
      en op basis daarvan wordt het e-mailadres van de juiste afdeling gezet in de
      gebruikersvariabele. Deze variabele kan vervolgens gebruikt worden in de
      registratie-instellingen.

      In dit voorbeeld wordt het e-mailadres ingesteld op ``a@example.com`` zodra
      de bronpagina de URL ``*/test*`` bevat, en in alle andere gevallen wordt de
      standaardwaarde ``b@example.com`` gebruikt.

#. Klik onderaan op **Opslaan** om het formulier volledig op te slaan.

Je kan nu het formulier bekijken.

Dit formulier is erg geschikt voor eenvoudige contactformulieren die op pagina's van de
gemeentewebsite ingesloten worden. Op basis van de ``form_url``-variabele kan de
inzending meteen naar de juiste afdeling gerouteerd worden voor de opvolging en
behandeling.
