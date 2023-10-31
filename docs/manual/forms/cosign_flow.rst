.. _manual_cosign_flow:

Mede-ondertekenen
=================

Open Formulieren ondersteunt formulieren waarin een tweede persoon een inzending moet ondertekenen voor deze
verwerkt wordt, zoals een partner of voogd. Er is dus een extra persoon betrokken naast de invuller van het formulier.

Flow
----

De mede-ondertekenen flow is hieronder beschreven. Persoon 1 is de persoon die als eerste het formulier invult.
Persoon 2 is de mede-ondertekenaar.

#. Persoon 1 logt in om het formulier te beginnen.
#. In het formulier bevindt zich een "Mede-ondertekenen" component. Hier kan persoon 1 het e-mailadres van persoon 2
   opgeven.
#. Zodra het formulier ingestuurd wordt, krijgt persoon 1 een bevestigingsmail (als deze ingeschakeld is).
#. Persoon 2 ontvangt een e-mail met het verzoek om het formulier te mede-ondertekenen. De e-mail
   bevat of een directe link óf instructies om het formulier te openen (afhankelijk van de instelling in de
   **Algemene configuratie**). In de e-mail staat een verificatiecode voor de inzending.
#. Persoon 2 navigeert naar de startpagina van het formulier en logt in met de
   **Log in om het formulier mede te ondertekenen**-knop.

   .. image:: _assets/cosign_buttons.png
       :width: 100%

#. Vervolgens moet persoon 2 de verificatiecode uit de e-mail invullen. Bij een geldige code ziet de gebruiker een
   overzicht van de ingevulde gegevens.
#. Indien relevant, dan moet persoon 2 het privacybeleid en/of de verklaring van waarheid accepteren (dit is een
   formulierinstelling). Daarna bevestigt de gebruiker de mede-ondertekening.
#. Persoon 1 en persoon 2 ontvangen daarna allebei een bevestigingsmail.
#. De inzending wordt nu verwerkt met de gekoppelde registratieplugin (dus pas ná het mede-ondertekenen).


