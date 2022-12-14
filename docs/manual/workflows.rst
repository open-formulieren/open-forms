.. _manual_workflows:

===============
Beheerprocessen
===============

Formulieren worden gemaakt, gepubliceerd, bijgewerkt, vervangen en eventueel
uitgefaseerd. Hieronder staan de typische beheerprocessen voor formulieren die
u kunt gebruiken om de levensloop van een formulier te optimaliseren.

Essentieel bij het beheer zijn 2 opties:

* **Actief** geeft de globale beschikbaarheid aan.
* **Onderhoudsmodus** geeft aan dat een formulier tijdelijk niet beschikbaar 
  is.

Zodra een formulier *niet actief* of in *onderhoudsmodus* staat, dan is het
formulier voor reguliere gebruikers direct niet meer te gebruiken en lopende 
sessies kunnen niet worden afgemaakt. In het geval een formulier *niet actief*
is, dan geldt dit ook voor beheerders. In *onderhoudsmodus* kunnen beheerders
nog wel het formulier starten, invullen en verzenden.


Nieuw formulier maken
=====================

Als u het formulier direct op de productieomgeving bouwt, wilt u niet dat 
reguliere gebruikers dit formulier al kunnen benaderen of invullen.

Zet de optie **Onderhoudsmodus** aan voordat u de eerste maal op **Opslaan** 
klikt. Het formulier is hierdoor enkel door te starten door beheerders. 
Doorloop altijd eerst zelf het formulier voordat u een formulier actief maakt.

.. note::
    
   Als u een nieuw formulier importeert staat de optie **Actief** automatisch
   uit, en het geïmporteerde formulier kan dus niet benaderd worden door
   reguliere gebruikers en beheerders.


Bestaand formulier bijwerken in de beheerinterface
==================================================

Als een formulier in gebruik is op de productieomgeving, wilt u het formulier
eventueel bijwerken. Gebruikers die op dat moment bezig zijn wilt u zo min 
mogelijk hinderen.

Zet de optie **Onderhoudsmodus** aan en klik op **Opslaan**. Wijzig vervolgens 
het formulier waar nodig. U kunt de wijzigingen in het formulier als beheerder 
nog wel bekijken, maar reguliere gebruikers kunnen het formulier niet 
gebruiken.

.. note::

   Als de wijzigingen niet de structuur van het formulier wijzigen, zoals een 
   veld of stap toevoegen dan wel verwijderen, dan kunt u het formulier gewoon 
   wijzigen en opslaan, zonder dit formulier eerst op inactief te zetten.

   Lopende sessies blijven gewoon bestaan en ondervinden geen hinder.


Bestaande formulieren bijwerken middels import
==============================================

Als u een formulier heeft gemaakt op een andere omgeving (bijvoorbeeld een 
test- of acceptatieomgeving) en deze wilt importeren om een bestaand formulier
te vervangen, dan is dat niet direct mogelijk.

U moet rekening houden met de volgende complicaties:

* Een formulier importeren met dezelfde naam, overschrijft nooit een bestaand
  formulier in Open Formulieren. Er komen simpelweg 2 formulieren met dezelfde
  naam.
* De URL van een formulier moet uniek zijn. Om deze reden kunnen 2 formulieren
  niet dezelfde URL hebben. Als de URL van een geïmporteerd formulier al in
  gebruik is, dan krijgt het geïmporteerde formulier een iets andere URL.
* De URL van formulierdefinities (stappen) moeten uniek zijn. Als er al een 
  formulierdefinitie bestaat met dezelfde URL, dan krijgt de formulierdefinitie
  van het geïmporteerde formulier een iets andere URL.

U kunt de volgende acties uitvoeren om toch een bestaand formulier te 
vervangen middels een import:

#. Open het bestaande formulier in de beheerinterface.
#. Zet de optie **Actief** uit en wijzig de naam zodat er *(oud)* achter komt 
   te staan.
#. Wijzig ook de URL zodat er *-oud* achter komt te staan.
#. Wijzig bij alle formulierstappen, de URL zodat ook hier overal *-oud* achter 
   komt te staan. Heeft u **Herbruikbare** formulierstappen? Wijzig hier de URL 
   dan niet om wijzigingen aan andere formulieren te voorkomen.
#. Sla het formulier op. Het formulier is nu niet meer actief.
#. Importeer het het vervangende formulier.
#. Pas eventueel de URLs aan van de formulierstappen die herbruikbaar zijn om
   mooiere URLs te gebruiken.
#. Configureer het formulier verder met alle informatie die niet is meegekomen 
   met het importeren.
#. Zet het geïmporteerde formulier op **Actief** en sla het formulier op.
