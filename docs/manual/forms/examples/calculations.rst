.. _example_calculations:

==========================
Formulier met berekeningen
==========================

In dit voorbeeld maken we een fictief formulier bestaande uit 1 stap, waarbij
meerdere velden worden gebruikt voor berekeningen.

In dit voorbeeld gaan we er van uit dat u een
:ref:`formulier met eenvoudige logica <example_logic_rules>` kan maken en dat
u op de hoogte bent van hoe :ref:`logica <manual_logic>` werkt.

Formulier maken
===============

#. Maak een formulier aan met de volgende gegevens:

   * **Naam**: Berekeningen demo

#. Klik op het tabblad **Stappen en velden**.
#. Klik aan de linkerkant op **Stap toevoegen** en selecteer **Maak een nieuwe
   formulierdefinitie**.
#. Onder de sectie **(Herbruikbare) stapgegevens** vul het volgende in:

   * **Naam**: Stap met berekeningen

#. Scroll naar de sectie **Velden**.
#. Sleep een **Getal** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Number A

   Herhaal deze stap nog 2 keer, maar gebruik dan als label **Number B** en **Number C**.

#. Sleep een **Getal** component op het witte vlak, vul de volgende
   gegevens in en druk daarna op **Opslaan**:

   * **Label**: Number A+B*C

#. Druk daarna op **Opslaan en opnieuw bewerken**.
#. Klik op het tabblad **Logica** en voeg een geavanceerde regel toe met de volgende trigger:

    .. code-block:: json

        {
          "or": [
            {
              "!=": [
                {
                  "var": "numberA"
                },
                null
              ]
            },
            {
              "!=": [
                {
                  "var": "numberB"
                },
                null
              ]
            },
            {
              "!=": [
                {
                  "var": "numberC"
                },
                null
              ]
            }
          ]
        }

   en de volgende actie: **wijzig de waarde van een variabel/component**, **Number A+B\*C**, met de waarde:

    .. code-block:: json

        {
          "+": [
            {
              "var": "numberA"
            },
            {
              "*": [
                {
                  "var": "numberB"
                },
                {
                  "var": "numberC"
                }
              ]
            }
          ]
        }

   Deze actie vermeningvuldigt **Number B** en **Number C** en voegt de resultaat aan **Number A**.


U kunt nu het formulier bekijken. Als u waarden invult in de velden **Number A**, **Number B** en **Number C**
dan verschijnt het resultaat van de berekening in het veld **Number A+B\*C**
