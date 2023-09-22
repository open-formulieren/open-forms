"""
Provide Haal Centraal shared functionality.

`Haal Centraal`_ is an initiative to expose Dutch-government data via a number of APIs,
in a centralized way ("direct bij de bron"). It is often confused or merged with the
"Haal Centraal BRP Persoon bevragen", but this is really just a single API under the
Haal Centraal umbrella.

This package provides API configuration and (base) client implementations for those
Haal Centraal API's that we consume in Open Forms.

.. note:: Technically the BAG API (see :module:`openforms.contrib.kadaster.clients.bag`)
   also falls under the umbrella of Haal Centraal, however all API root URLs still point
   to ``kadaster.nl`` domains and as such the code is organized in
   ``openforms.contrib.kadaster``.

.. _Haal Centraal: https://vng-realisatie.github.io/Haal-Centraal/
"""
