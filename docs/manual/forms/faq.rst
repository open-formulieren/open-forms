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
