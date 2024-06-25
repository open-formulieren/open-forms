.. _manual_authenticatie:

========================
Authenticatie (inloggen)
========================

Om van :ref:`voorinvullen (prefill) <example_prefill>` gebruik te kunnen maken, moeten
gebruikers ingelogd zijn op het formulier. Als formulierbouwer kan je zelf aangeven
of inloggen verplicht, mogelijk of niet mogelijk is:

* je kan aangeven welke authenticatiemethoden beschikbaar zijn - zodra je hier één
  optie aanvinkt, is inloggen op het formulier mogelijk
* je kan stappen markeren als "Inloggen verplicht" - zodra één stap zodanig gemarkeerd
  is, dan is inloggen verplicht

Inlogmethoden
=============

Open Formulieren biedt inlogopties aan via een modulair systeem, maar grofweg zijn deze
onder te verdelen in:

* DigiD
* eHerkenning/eIDAS
* Medewerkerlogin (als ambtenaar bij de gemeente, bijvoorbeeld)

Hiervan zijn verschillende smaken beschikbaar, en elke inlogmethode geeft aan wat voor
identificatiegegeven beschikbaar komt, zoals BSN of KVK-nummer.

Machtigen/vertegenwoordiging
=============================

Machtigingen (vrijwillig dan wel niet-vrijwillig) komen voor als varianten van
DigiD/eHerkenning inlogmethoden en kunnen verwarrend zijn. De verschillende
machtigingsvormen die Open Formulieren kent en ondersteunt zijn hieronder toegelicht.

DigiD Machtigen
---------------

Bij deze machtigingsvorm wordt een persoon gemachtigd om diensten af te nemen voor een
andere persoon, de vertegenwoordigde. Dit is altijd op basis van het BSN van beide
personen, en de machtiging is afgegeven op een specifieke dienst of dienstenset.

.. note:: Technische opmerking: DigiD Machtigen is enkel mogelijk via het OpenID
   Connect protocol. Dit kan (nog) niet met een standaard-DigiD-aansluiting.

eHerkenning
-----------

Bij eHerkenning worden diensten afgenomen voor een bedrijf. Op dit moment ondersteunen
we enkel identificatie van diensten op basis van KVK-nummer (en niet op basis van RSIN).

Bij eHerkenning heeft één of meerdere medewerkers van het bedrijf een persoonlijk
"middel" waarmee ze het bedrijf vertegenwoordigen. Bij een dergelijke inlog is er altijd
sprake van de "legal subject", ofwel het bedrijf dat vertegenwoordigd wordt, en van
de "acting subject" (handelende persoon), ofwel "de persoon aan de knoppen".

De identificatie van de handelende persoon is stabiel - we kunnen dus bepalen of iets
door dezelfde medewerker gedaan is, maar verder zijn er geen gegevens af te leiden van
deze persoon - de identificatie is versleuteld.

eHerkenning bewindvoering
-------------------------

Gelijksoortige (maar nog niet beschikbare) machtigingsvormen zijn curatele en
mentorschap. Bij deze machtigingsvorm wordt de machtiging door een juridische instantie
opgelegd. Er kunnen privépersonen zijn die bewind voeren, maar dit kan ook door een
bedrijf gebeuren.

Open Formulieren ondersteunt momenteel enkel bewindvoering door een bedrijf. De
vertegenwoordigde wordt geïdentificeerd op basis van hun BSN.

Ook hier is er nog steeds sprake van een handelende persoon die het bedrijf
vertegenwoordigt, en het bedrijf vertegenwoordigt op zijn beurt weer de persoon waarover
bewind gevoerd wordt.
