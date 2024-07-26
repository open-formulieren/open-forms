.. _developers_roadmap:

Roadmap
=======

The Open Forms roadmap describes broader topics that will be picked up in the
nearby future.

As with most software projects, the codebase of Open Forms grows dynamically, driven
by user stories, user feedback and developer experience. Inevitably, some technical
debt is created and needs to be addressed. This is included in our roadmap to keep
Open Forms a healthy and developer-friendly project.

The roadmap also offers some context to smaller issues that might linger a bit, waiting
to be picked up in a broader topic.

Backend
-------

**Formio integration rework**

Status: in progress

Currently, Open Forms is tightly coupled with Formio.js. There are a number of codepaths
that directly introspect Formio definitions in places you wouldn't immediately expect,
leading to code that is hard to maintain and reducing flexibility in the available
components.

The rework still only aims at supporting Formio.js, but the integration will be scoped
to a single ``openforms.formio`` package. All other apps/modules/packages shall operate
on an abstraction on top of that. This should make it easier to develop on Open Forms
without intricate Formio.js knowledge.

**Template context rework**

Status: not planned yet

The Django template system is used in a number of places, such as confirmation e-mails,
confirmation page content blocks etc. These templates are evaluated with the submission
data.

The context for these templates requires some server-side controlled variables and the
submission data is injected on top of that, polluting the top-level context namespace.

We should make an effort to migrate this data (with keys controlled by form designers)
into a separate namespace to prevent surprises. This is a tricky change, as it may be a
breaking change for existing templates.

This also aligns with the following topic.

**API documentation**

Status: not planned yet

Open Forms makes extensive use of JSONField in the database, which by default doesn't
provide much information in the API schema. On top of that, we typically *do* actually
validate the schema of this JSON data using serializers, but this is not always
reflected in the generated OAS 3 API schema.

Part of the reason for that is that the schema varies with a selected plugin, so we are
looking at polymorphic schema's. To provide better upfront documentation, we should
explicitly declare these serializers as being polymorphic through ``drf-polymorphic``.

**API formatting**

Status: not planned yet

Python's style guide prescribes (variable) names in ``snake_case``, while the Javascript
world (and JSON APIs) typically use ``camelCase``. Additionally, the Dutch API strategy
settles on ``camelCase``.

Open Forms uses a library ``djangorestframework-camel-case`` to convert between the two,
but this proves to be challenging when dealing with user-supplied keys or ``JSONField``
content that should be left untouched.

The drf-camel-case library has some options to (globally) ignore some field names, but
this is not flexible enough and will cause confusion later down the road.

We should explore possible improvements to drf-camel-case or completely other approaches
do deal with the camel-case/underscore conversions.

**Health checking/plugin status check**

Status: not planned yet

The internal page to check the (configuration) status of various plugins currently
checks all plugins sequentially and leads to a slow page.

This should be optimized to only consider enabled plugins and work asynchronously.
