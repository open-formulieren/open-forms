==========
Open Forms
==========

:Version: 0.1.0
:Source: https://github.com/maykinmedia/open-forms
:Keywords: e-Formulieren, Common Ground, FormIO, API
:PythonVersion: 3.7

|build-status| |docs| |coverage| |black| |docker|

Easily create and publish smart forms (`Nederlandse versie`_)

Developed by `Maykin Media B.V.`_.


.. warning:: The master branch is currently very unstable. Use the git tag
   ``still-functional`` if you need a working backend + frontend.


Introduction
============

Using Open Forms, administrators can quickly create powerful and smart forms
that are exposed via an API. With the included webcomponent, personalized forms
can be retrieved and shown to the user. The form blends in with an
existing website using various styling options. Form fields are prefilled
whenever possible and personalized choices are shown depending on the user if
logged in using DigiD.

Open Forms is developed in line with the `Common Ground`_ principles,
specificly for municipalities and with a strong focus on usability for both
the civilian users and the administrator.

Form submissions can be added as document to a "Zaak" in, for example,
`Open Zaak`_, or used as input for a BPMN process in `Camunda`_ or
`Alfresco Process Services`_.

Open Forms supports among others:

* Fast and easy form building
* Forms can be styled to blend in with your website
* Login using DigiD
* Smart components show family members retrieved from the BRP `BRP`_ or owned
  properties from the BAG
* Prefilled form fields if the information is already known
* Store answers in a database, send them to a process in `Camunda`_ or attach
  as a document with a "`Zaak`_"
* Link forms to products
* Calculate costs and payment options
* Modern REST API to access forms and send in submissions


.. _`Camunda`: https://camunda.com/
.. _`Alfresco Process Services`: https://www.alfresco.com/bpm-software
.. _`Common Ground`: https://commonground.nl/
.. _`BRP`: https://open-personen.readthedocs.io/
.. _`Open Zaak`: https://open-zaak.readthedocs.io/
.. _`Zaak`: https://open-zaak.readthedocs.io/


References
==========

* `Issues <https://github.com/maykinmedia/open-personen/issues>`_
* `Code <https://github.com/maykinmedia/open-personen>`_
* `Community <https://commonground.nl/groups/view/54477955/open-personen>`_
* `Documentation <https://open-personen.readthedocs.io/>`_

Licence
=======

Copyright © Maykin Media B.V., 2020

.. _`Nederlandse versie`: README.NL.rst

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
