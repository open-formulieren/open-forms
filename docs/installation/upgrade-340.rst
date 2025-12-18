.. _installation_upgrade_340:

===================================
Upgrade details to Open Forms 3.4.0
===================================

Open Forms 3.4.0 is a minor, backwards compatible feature release. However, we recommend
you process these release notes as soon as possible to prevent future surprises. We also
want to provide some context and background information that can help diagnose possible
problems after upgrading.

Finally, this release deprecates a number of old functionalities that will be removed
in Open Forms 4.0. At the time of writing, we expect the new major version with breaking
changes early in Q3 2026.

New renderer
============

.. note:: Relevant for: functional administrators, theme designers, devops.

Historically, we have built the frontend of Open Forms around `Form.io <https://form.io/>`_,
which has been essential to the success of Open Forms. However, over time we've been
running into more and more limitations of the Javascript library, including performance
issues.

Over the past months, we've worked on our own implementation of this library, tailored
to the needs of Open Forms. It is now feature complete and stable, and included from Open
Forms 3.4.0 onwards, but not yet battle tested.

Open Forms 3.4.0 includes both the old and new renderer implementations, defaulting to
the old one. The new renderer can be enabled on an individual form basis, and we provide
tooling to bulk-enable the new renderer via the command line.

In an app container, execute:

.. code-block:: bash

    python /app/src/manage.py set_forms_new_renderer_enabled --state=enabled

To disable it globally, replace ``enabled`` with ``disabled``.

We chose those defaults to make gradual rollouts possible and prevent service
disruptions. However, we encourage everyone to start testing existing forms with the new
renderer and report any bugs you may encounter! It is ready for production usage, with
*some* caveats described below.

The old renderer will be removed in a future release.

AddressNL component
-------------------

The ``addressNL`` component was introduced a while ago but didn't yet perform as
desired. We have addressed many issues in the new renderer, but not all of them yet,
especially the combination with address autofill based on postcode and house number.

We recommend to wait a little longer before enabling this component in production.

Address autofill functionality
------------------------------

The old renderer supports autofilling address details from the BAG APIs, via configuration
options on the ``textfield`` component. This feature is not implemented in the new
renderer, as the ``addressNL`` component is supposed to replace this.

However, due to the known problems in that component, we recommend sticking to the old
renderer if you have forms that make use of the autofill behaviour. We'll keep you
updated when the issues are resolved and the ``addressNL`` component can be instead
instead.

HTML escaping
-------------

Formio.js is quite tolerant in interpreting text content as HTML - in the old renderer
HTML markup tags like "bold", "italic" but also hyperlinks have typically been displayed,
even though we never officially supported this.

The new renderer is much stricter with regards to escaping HTML, which is a security
feature to prevent cross-site scripting vulnerabilities.

This tends to affect the following places:

* component labels
* component descriptions
* component tooltips

Our recommendation is to review forms and remove the HTML. If rich text formatting is
absolutely necessary, consider putting it in a ``content`` component which supports
rich text formatting.

File upload component
---------------------

The UI of the file upload component is heavily revised in the new renderer. We made
numerous changes to improve screen reader support as well, but it's always possible
that we missed certain cases. If you perform accessibility audits and have findings,
please let us know!

Additionally, the visual appearance has been updated. The Open Forms backend and default
theme contain shims for backwards compatibility, but if you make use of embedding on
external (CMS) pages and use a custom theme, you will need to update your theme.

The available design tokens are documented in
`storybook <https://open-formulieren.github.io/formio-renderer/?path=/docs/component-registry-basic-file-theming--docs>`__.

NL Design System / custom themes
--------------------------------

In the new renderer we're leaning more on existing (community) components from NL
Design System, replacing own legacy implementations. There is a chance that your custom
theme does not specify the necessary design tokens for those components. The Open Forms
backend includes shims for backwards compatibility.

We have documented the relevant design tokens for theming in
`storybook <https://open-formulieren.github.io/formio-renderer/?path=/docs/introduction--docs>`__.
You can enter "Theming" in the search bar to discover the relevant documentation pages.

You can also use the `changeset <https://github.com/open-formulieren/design-tokens/compare/0.61.0...0.66.0>`_
of our default theme as a reference.

Affected components
^^^^^^^^^^^^^^^^^^^

**Tooltips in labels**

Icons now use the ``utrecht-icon`` component, which may break themes due to existing or
unset ``icon-size`` design token.

**Icons in buttons**

Icons now use the ``utrecht-icon`` component, which may break themes due to existing or
unset ``icon-size`` design token. Additionally, the alignment of the icon within a
button may require some CSS overrides.

**File upload**

The ``file`` component has been rebuilt from scratch, and introduces the following
UI components with their set of design tokens:

* ``openforms-file-upload``
* ``openforms-upload-input``
* ``openforms-uploaded-files-list``
* ``openforms-uploaded-file``

The backwards compatibility shims leverage the legacy ``of.file-upload.drop-area.padding``
and ``of.field-border.color`` tokens and otherwise set some hardcoded defaults to keep
the visual appearance similar.

**Calendar**

We've replaced the Flatpickr datepicker with an alternative based on the
``utrecht-calendar`` component, which requires design tokens to be specified for:

* ``utrecht-calendar``
* ``utrecht-button``

The backwards compatibility shims roughly replicate the appearance from Flatpickr.

**Input group**

The input group component is used for fields where parts of the input can be individually
specified, such as day/month/year of a date field. Specify design tokens for the
``openforms-input-group`` component to control the spacing between inputs and alignment
of elements.

**Form controls**

We've updated the semantics of read-only fields - due to Formio.js implementation details
those fields were marked as ``disabled`` causing them to not be reachable via keyboard
navigation and not being "visible" to screen readers. Now the read-only configuration is
true ``readonly`` behaviour, which uses different design tokens.

Please make sure you have declared values for the ``utrecht-textbox-read-only-*`` and/or
``utrecht-form-control-read-only-*`` design tokens. Our backend includes shims for
backwards compatibility.

Backend data types and logic evaluation rework
==============================================

.. note:: Relevant for: functional administrators.

Beginning 2025, we've started an ambitious rework of the internal logic and
data-processing engine of Open Forms with the end goal of significantly improving the
perceived performance for end users filling out forms.

This requires us to touch many moving parts of Open Forms, all while being backwards
compatible. We've carefully planned out the various steps necessary to achieve this and
are on track, but unfortunately unexpected bugs *do* happen because of this rework,
despite our extensive automated test suite. This can be attributed to implicit
assumptions no longer holding true, and these are hard to account for in existing tests.

The data types rework results in the backend having rich type information about the
form submission data. For example, whereas a date is transported over the wire as the
string ``2026-01-04``, in the backend this becomes an actual ``date`` instance, like
``datetime.date(2026, 1, 5)``. This affects your forms anywhere the submission data
is processed, most notably where user-supplied templates are evaluated with form
submission data, like:

* Objects API registration plugin (legacy)
* Confirmation page / email templates
* Cosign-related templates
* Form logic performing calculations on submission data

We urge you to extensively test existing forms before upgrading production, testing all
possible combinations, and please report any bugs/situations you encounter. We would
love to ship tooling to faciltate automatic updating as well, so suggestions are welcome.

Observability
=============

.. note:: Relevant for: devops.

We're still working on observability improvements to facilitate monitoring the operational
side of Open Forms in dashboards like Grafana. The current status of the individual
components is:

* logging: stable core - we output structured logs. We're plannning some more internal
  rework for legacy logging systems to build on top of the core.
* metrics: semi-stable. We're planning to generalize some metrics across different
  applications, so some more renames may happen in a future release.
* (distributed) tracing: bare bones, unstable. To be fleshed out in future releases.
* Elastic APM: stable, but will eventually be replaced with native OTel tracing.

Renamed metrics
---------------

Open Forms 3.3 added application metrics. It was pointed out to us that the metrics did
not comply with the official OTel naming conventions, so in Open Forms 3.4 the metric
names have been updated.

You can find the updated names in the :ref:`metrics documentation <installation_observability_metrics>`.

JCC appointments
================

.. note:: Relevant for: functional administrators.

The JCC plugin for appointments in Open Forms stops working as of Jan. 1st 2026 due to
JCC shutting down their SOAP service.

Work is underway to replace this with their RESTful API service. This shall be included
in the future 3.5.0 release.

Ogone payments
==============

.. note:: Relevant for: functional administrators.

The Ogone (legacy) payment provider stops working as of Jan. 1st 2026 due to Worldline
shutting down those operations. The replacement is the "Worldline payment plugin", which
was released in Open Forms 3.3.0.

Deprecations
============

.. note:: Relevant for: functional administrators.

The features below are deprecated as of the Open Forms 3.4.0 release, meaning they will
only receive support for critical bugs. They will be removed in Open Forms 4.0
*at the latest* (complying with our versioning policy).

Old renderer
------------

The old renderer (=current) is guaranteed to remain available in Open Forms 3.4.0. If
the new renderer is successful enough, it may be removed as soon as Open Forms 3.5.0,
as the functionality should remain backwards compatible.

We plan to remove the styling shims for backwards compatibility in Open Forms 4.0 as
well.

Ogone payment plugin
--------------------

Due to Worldline shutting down the service, the plugin code for it will be removed.
Effectively as of Open Forms 3.4.0 we expect this plugin to not function anymore.

Usage the Worldline plugin instead.

JCC SOAP service
----------------

Due to JCC shutting down the service, the plugin code for it will be removed.
Effectively as of Open Forms 3.4.0 we expect this plugin to not function anymore.

Starting from Open Forms 3.5.0, you can use the REST-based plugin instead.
