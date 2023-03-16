.. _faq:

==========================
Vaak voorkomende problemen
==========================

Advanced logica regels
======================

Selectievakjes
--------------

Selectievakjes in FormIO hebben een 'deelstructuur'. Bijvoorbeeld, als er een selectievakjes component met key
``selectBoxes`` is en mogelijke waarden ``a``, ``b`` en ``c``, dan heeft de data de structuur:

.. code-block:: json

    {
        "a": false,
        "b": false,
        "c": false
    }

Als het ``a``-vakje is aangevinkt, heeft de inzending data de volgende structuur:

.. code-block:: json

    {
        "a": true,
        "b": false,
        "c": false
    }

Voor geavanceerde logica regels die afhankelijk zijn van de waarden van een selectievakjescomponent, moet de trigger
de volgende structuur hebben:

.. code-block:: json

    {
        "==": [
            {
                "var": "selectBoxes.a"
            },
            true
        ]
    }

Deze trigger betekent "Als het vakje ``a`` aangevinkt is".

Als je gebruik maakt van eenvoudige regels, dan wordt deze structuur automatisch gebruikt.

Ogone simulator "Method not allowed"
====================================

Wanneer je de Igenico/Ogone iDeal betaalsimulator gebruikt kunnen sommige combinaties
van failure/exception en "Terug"-knop tot fouten leiden in Open Formulieren, zoals:

.. code-block:: json

    {
        "type": "https://formulieren-xxxxxxxxx.nl/fouten/MethodNotAllowed/",
        "code": "method_not_allowed",
        "title": "Methode \"{method}\" niet toegestaan.",
        "status": 405,
        "detail": "Methode \"POST\" niet toegestaan.",
        "instance": "urn:uuid:dd1ce704-e86f-xxxx-xxxx-af9f8e3d740f"
    }

Dit speelt niet als je op de "Annuleren" knop drukt in plaats van "Terug".

Dit is een bekend probleem in de Ogone simulator wat niet opgelost gaat worden. Ons is
verzekerd dat dit in de productieomgeving niet speelt.

Technische details voor ontwikkelaars zijn beschikbaar in Github issue #2362.
