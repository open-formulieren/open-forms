.. _manual_forms_variables:

===================
Formuliervariabelen
===================

Variabelen vormen een krachtige manier om verschillende gegevens in een formulier
bij elkaar te laten komen. U kunt :ref:`variabelen gebruiken <manual_forms_form_fields_variables_usage>`
in logica, in andere velden, of om interne gegevens op te slaan die niet voor
de eindgebruiker bedoeld zijn.

Er zijn 3 soorten variabelen:

Formuliervariabelen
===================

Alle velden in het formulier zijn beschikbaar als variabele. De
eigenschapsnaam van een veld wordt gebruikt als variabele. Dit gebeurt
automatisch.

Gebruikersvariabelen
====================

Zelf te beheren variabelen die niet gekoppeld zijn aan een specifiek
formulierveld. U kunt hier bijvoorbeeld waarden opslaan die door logica worden
verkregen of uit externe koppelingen opgehaald worden.

.. _manual_forms_variables_static_variables:

Vaste variabelen
================

Een vaste lijst met variabelen die beschikbaar zijn in alle stappen van het formulier.
Afhankelijk van het type formulier zijn variabelen wel of niet voorzien van een
waarde.

======================= ========= =========================== =========================================================================
Variabele               Type      Voorbeeldwaarde             Toelichting
======================= ========= =========================== =========================================================================
now                     datetime  ``2022-09-09 18:29:00``     Datum van vandaag. Hier zijn
                                                              :ref:`verschillende weergaven <manual_templates_formatting_of_variables>`
                                                              van mogelijk.
                                                              Seconden en milliseconden zijn altijd 0.
environment             string    ``production``              De waarde die tijdens de installatie gezet is als
                                                              ``ENVIRONMENT``. Zie:
                                                              :ref:`installation_environment_config`.
form_name               string    ``Paspoort aanvragen``      De naam van het formulier.
form_id                 string    ``1c453fc8-b10f-4510-``...  Het unieke ID van het formulier.
auth                    object                                Een verzameling van authenticatie gegevens. Zie
                                                              hieronder.
auth.plugin             string    ``digid``                   De systeemnaam van de gebruikte authenticatie plugin.
auth.value              string    ``111222333``               De identificerende waarde in het ``attribute`` van de
                                                              authenticatie plugin.
auth.additional_claims  object    ``{"name": "...", ...}``    De aanvullende authenticatie gegevens, voornamelijk
                                                              gebruikt bij Yivi en eIDAS authenticatie.
auth_type               string    ``bsn``                     Kan de waarden ``bsn``, ``kvk`` of ``pseudo`` hebben.
auth_bsn                string    ``111222333``               De waarde van ``auth.value`` indien ``auth_type`` als
                                                              waarde ``bsn`` heeft. Anders leeg.
auth_kvk                string    ``90001354``                De waarde van ``auth.value`` indien ``auth_type`` als
                                                              waarde ``kvk`` heeft. Anders leeg.
auth_pseudo             string    ``a8bfe7a293dd``...         De waarde van ``auth.value`` indien ``auth_type`` als
                                                              waarde ``pseudo`` heeft. Anders leeg.
auth_additional_claims  object    ``{"name": "...", ...}``    De waarde van ``auth.additional_claims``.
auth_context            object    ``{"source": "...", ...}``  De volledige authenticatiecontext, met
                                                              machtigingsinformatie. Zie
                                                              :ref:`manual_forms_variables_auth_context` voor de
                                                              beschrijving en individuele elementen als vaste
                                                              variabelen.
======================= ========= =========================== =========================================================================

**Verouderde variabelen**

Deze variabelen zijn nog wel beschikbaar, maar we raden aan om deze niet meer te
gebruiken. In versie 4.0 van Open Formulieren kunnen deze verwijderd worden.

=============== ========= =========================== =========================================================================
Variabele       Type      Voorbeeldwaarde             Toelichting
=============== ========= =========================== =========================================================================
auth.attribute  string    ``bsn``                     Kan de waarden ``bsn``, ``kvk`` of ``pseudo`` hebben (verouderd,
                                                      gebruik bij voorkeur ``auth_type``).
=============== ========= =========================== =========================================================================

.. note::
   Bij authenticatie met de Yivi en eIDAS plugins, worden eventuele aanvullende gegevens beschikbaar gesteld onder
   ``auth.additional_claims`` en ``auth_additional_claims``. Om deze gegevens te kunnen gebruiken in
   JsonLogic-expressies, zijn punten in de attribuutnamen vervangen met liggende streepjes.

   Bijvoorbeeld: als je het Yivi attribuut ``pbdf.gemeente.personalData.over18`` gebruikt in een formulier, kan je deze
   als ``auth.additional_claims.pbdf_gemeente_personalData_over18`` gebruiken in JsonLogic en in overige sjablonen.


.. _manual_forms_variables_auth_context:

Authenticatiecontext
--------------------

De "authenticatie context" bevat alle beschikbare informatie over *hoe* iemand ingelogd
is op een formulier. Deze bundel informatie is beschikbaar in de vaste variabele
``auth_context``.

Wanneer er niet ingelogd is op het formulier, dan is de waarde van deze variabele
``null``.

.. note::

    De ``auth_context`` variabele gaat op termijn de ``auth`` variabele vervangen,
    maar voorlopig wordt deze laatste niet verwijderd.

    Tip: in plaats van ``auth.plugin`` kan je beter ``auth_context_source`` of
    ``auth_type`` gebruiken - de eerste is minder flexibel/uitwisselbaar, terwijl de
    tweede wel goed de semantische betekenis bevat of het om een burger of bedrijf gaat.

.. versionremoved:: 3.0

    De ``auth.machtigen`` variabele is verwijderd omdat de structuur hiervan vaag en
    onbetrouwbaar was. Gebruik ``auth_context`` in de plaats.

De variabele bevat een bak aan informatie, gestructureerd volgens het
authenticatiecontextdatamodel_. De structuur is als volgt:

.. _authenticatiecontextdatamodel: https://app.gitbook.com/o/xSFlMqbR6wFN2VhQWOy6/s/VabqDNWmqXP8aggdbh1j/patronen/machtigen

.. code-block:: json

    {
        "source": "string",
        "levelOfAssurance": "string",
        "representee": {
            "identifierType": "string",
            "identifier": "string"
        },
        "authorizee": {
            "legalSubject": {
                "identifierType": "string",
                "identifier": "string",
                "branchNumber": "string",
                "additionalInformation": "object",
                "companyName": "string",
                "firstName": "string",
                "familyName": "string",
                "dateOfBirth": "string",
            },
            "actingSubject": {
                "identifierType": "string",
                "identifier": "string",
                "firstName": "string",
                "familyName": "string",
                "dateOfBirth": "string",
            }
        },
        "mandate": {
            "role": "string",
            "services": [
                {
                    "id": "string",
                    "uuid": "string"
                }
            ]
        }
    }

Merk op dat niet alle attributen aanwezig zijn, dit hangt af van het inlogmiddel (
DigiD, eHerkenning) en of er wel/niet sprake is van een machtiging én de soort
machtiging.

De volgende attributen zijn gegarandeerd aanwezig:

* ``source``, mogelijk lege string als waarde
* ``levelOfAssurance``, mogelijk lege string als waarde
* ``authorizee``
* ``authorizee.legalSubject``
* ``authorizee.legalSubject.identifierType``, mogelijk lege string als waarde
* ``authorizee.legalSubject.identifier``, mogelijk lege string als waarde

De onderdelen van deze structuur worden ook als individuele variabelen aangeboden:

``auth_context_source``
    Middel van inloggen: de waarde is ``digid`` of ``eherkenning``, of een lege string
    wanneer er geen informatie beschikbaar is.

``auth_context_loa``
    Betrouwbaarheidsniveau waarmee ingelogd is. Kan leeg zijn indien onbekend.

``auth_context_representee_identifier_type``
    Geeft aan of het om een BSN of KVK-nummer gaat, en bepaalt dus de soort
    vertegenwoordigde. Leeg indien onbekend of als er geen sprake is van machtigen.

``auth_context_representee_identifier``
    Identificatie van de vertegenwoordigde. Leeg indien onbekend of als er geen sprake
    is van machtigen.

``auth_context_legal_subject_identifier_type``
    Geeft aan of het om een BSN of KVK-nummer gaat, en bepaalt dus de soort
    (wettelijke) vertegenwoordigder (of de ingelogde persoon zelf indien er geen sprake
    is van vertegenwoordiging). Leeg indien het formulier zonder inloggen gestart is.

``auth_context_legal_subject_identifier``
    Identificatie van de (wettelijke) vertegenwoordiger. Leeg indien het formulier
    zonder inloggen gestart is.

``auth_context_branch_number``
    Vestigingsnummer waarvoor de medewerker ingelogd is. Leeg indien het geen
    eHerkenning-login betreft.

``auth_context_acting_subject_identifier_type``
    In de praktijk zal de waarde altijd ``opaque`` of leeg zijn. Geeft aan hoe de
    identificatie van de handelende persoon ("de persoon aan de knoppen")
    geïnterpreteerd moet worden.

``auth_context_acting_subject_identifier``
    Identificatie van de handelende persoon, leeg tenzij het een eHerkenning-login
    betreft. Deze waarde kan niet tot een persoon herleid worden (voor prefill), het
    is een versleutelde string. De waarde is wel gegarandeerd hetzelfde indien dezelfde
    medewerker weer inlogt voor hetzelfde bedrijf.
