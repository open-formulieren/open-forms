==========
Open Forms
==========

:Version: 0.1.0
:Source: https://github.com/maykinmedia/open-forms
:Keywords: e-Formulieren, Common Ground, FormIO, API
:PythonVersion: 3.7

|build-status| |docs| |coverage| |black| |docker|

Snel en eenvoudig slimme formulieren bouwen en publiceren. (`English version`_)

Ontwikkeld door `Maykin Media B.V.`_.


Introductie
===========

Met Open Forms kunnen beheerders snel slimme formulieren realiseren die 
ontsloten worden middels een API. Met het bijbehorende webcomponent kan het 
gepersonaliseerde formulier opgehaald en getoond worden aan de gebruiker, in de 
stijl van de gemeente. Hierbij zijn velden vooringevuld indien mogelijk en zijn
er keuzes beschikbaar afhankelijk van de, middels DigiD ingelogde, gebruiker.

Open Forms is ontwikkeld volgens de `Common Ground`_ principes, specifiek voor
gemeenten en met focus op gebruiksgemak voor zowel burger als beheerder.

Verstuurde formulieren kunnen direct als document worden toegevoegd aan een 
Zaak in bijv. `Open Zaak`_, of als input dienen voor een BPMN proces in 
`Camunda`_ of `Alfresco Process Services`_.

Open Forms ondersteund o.a.:

* Eenvoudig bouwen van formulieren
* Formulieren opmaken in eigen huisstijl
* Inloggen met DigiD
* Slimme componenten tonen familieleden uit de `BRP`_ of panden in eigendom uit
  de BAG
* Vooringevulde velden indien deze gegevens reeds bekend zijn
* Antwoorden opslaan in een database, doorsturen naar een proces aansturen 
  in `Camunda`_ of als document bij een `Zaak`_ bewaren
* Formulieren koppelen aan producten
* Kosten berekenen en betaalmogelijkheden
* Moderne REST API om formulieren te ontsluiten en op te sturen


.. _`Camunda`: https://camunda.com/
.. _`Alfresco Process Services`: https://www.alfresco.com/bpm-software
.. _`Common Ground`: https://commonground.nl/
.. _`BRP`: https://open-personen.readthedocs.io/
.. _`Open Zaak`: https://open-zaak.readthedocs.io/
.. _`Zaak`: https://open-zaak.readthedocs.io/


Links
=====

* `Issues <https://github.com/maykinmedia/open-forms/issues>`_
* `Code <https://github.com/maykinmedia/open-forms>`_
* `Community <https://commonground.nl/groups/view/54477660/open-forms>`_
* `Documentatie <https://open-forms.readthedocs.io/>`_


Licentie
========

Copyright © Maykin Media B.V., 2020

.. _`English version`: README.rst

.. _`Maykin Media B.V.`: https://www.maykinmedia.nl

.. |build-status| image:: https://travis-ci.org/maykinmedia/open-forms.svg?branch=master
    :alt: Build status
    :target: https://travis-ci.org/maykinmedia/open-forms

.. |docs| image:: https://readthedocs.org/projects/open-forms/badge/?version=latest
    :target: https://open-forms.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |coverage| image:: https://codecov.io/github/maykinmedia/open-forms/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage
    :target: https://codecov.io/gh/maykinmedia/open-forms

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |docker| image:: https://images.microbadger.com/badges/image/maykinmedia/open-forms.svg
    :target: https://microbadger.com/images/maykinmedia/open-forms
