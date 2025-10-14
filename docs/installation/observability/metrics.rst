.. _installation_observability_metrics:

=======
Metrics
=======

Open Forms produces application metrics (using Open Telemetry).

.. note:: The exact metric names that show up may be transformed, e.g. Prometheus replaces
   periods with underscores, and processing pipelines may add prefixes or suffixes.

.. important:: Some metrics are defined as "global scope".

   These metrics are typically derived from application state introspection, e.g. by
   performing database (read) queries to aggregate some information. Usually those
   correspond to an `Asynchronous Gauge <https://opentelemetry.io/docs/specs/otel/metrics/api/#asynchronous-gauge>`_.

   Multiple replicas and/or instances of the same service will produce the same values
   of the metrics. You need to apply some kind of aggregation to de-duplicate these
   values. The attribute ``scope="global"``  acts as a marker for these type of metrics.

   With PromQL for example, you can use ``avg`` on the assumption that all values will
   be equal, so the average will also be identical:

   .. code-block:: promql

       avg by (form_name, type) (otel_submissions_count{scope="global"})

Generic
=======

``http.server.duration``
    Captures how long each HTTP request took, in ms. The metric produces histogram data.

``http.server.request.duration`` (not active)
    The future replacement of ``http.server.duration``, in seconds. Currently not
    enabled, but the code is in the Open Telemetry SDK instrumentation already and could
    possibly be opted-in to.

Application specific
====================

.. versionchanged:: 3.4.0

    The metrics names have all been prefixed with the ``openforms`` namespace, and some
    metrics have some more renames to be better comply with the OTel naming conventions.

Accounts
--------

``openforms.auth.user_count``
    Reports the number of users in the database. This is a global metric, you must take
    care in de-duplicating results. Additional attributes are:

    - ``scope`` - fixed, set to ``global`` to enable de-duplication.
    - ``type`` - the user type. ``all``, ``staff`` or ``superuser``.

    Sample PromQL query:

    .. code-block:: promql

        max by (type) (last_over_time(
          otel_user_count{scope="global"}
          [1m]
        ))

``openforms.auth.login_failures``
    A counter incremented every time a user login fails (typically because of invalid
    credentials). Does not include the second factor, if enabled. Additional attributes:

    - ``http_target`` - the request path where the login failure occurred, if this
      happened in a request context.

``openforms.auth.user_lockouts``
    A counter incremented every time a user is locked out because they reached the
    maximum number of failed attempts. Additional attributes:

    - ``http_target`` - the request path where the login failure occurred, if this
      happened in a request context.
    - ``username`` - username of the user trying to log in.

``openforms.auth.logins``
    Counter incrementing on every successful login by a user. Additional attributes:

    - ``http_target`` - the request path where the login failure occurred, if this
      happened in a request context.
    - ``username`` - username of the user trying to log in.

``openforms.auth.logouts``
    Counter incrementing every time a user logs out. Additional attributes:

    - ``username`` - username of the user who logged out.

Forms
-----

Form metrics describe the forms defined by the organization. For submission statistics,
see the :ref:`Submission <installation_observability_metrics_submissions>` metrics.

``openforms.form_count``
    The total count of forms defined in the database, ignoring forms that have been
    moved into the trash. Additional attributes are:

    - ``scope`` - fixed, set to ``global`` to enable de-duplication.
    - ``type`` - one of ``total``, ``live``, ``translation_enabled``, ``is_appointment``
      or ``trash``. For all but ``trash`` the forms in the trash are excluded.

``openforms.form_component_count``
    Keeps track of how often a Formio component type is used in a form. This is only
    reported for live, non-appointment forms. Additional attributes are:

    - ``scope`` - fixed, set to ``global`` to enable de-duplication.
    - ``openforms.form.uuid`` - the unique database ID of the form.
    - ``openforms.form.name`` - the name of the form.
    - ``openforms.component.type`` - the Formio component type, e.g. ``textfield``, ``email``,
      ``selectboxes``...

.. _installation_observability_metrics_submissions:

Submissions
-----------

``openforms.submission.starts``
    Counts the number of submissions started by end-users. Additional attributes are:

    - ``openforms.form.uuid`` - the unique database ID of the form.
    - ``openforms.form.name`` - the name of the form that was submitted.
    - ``openforms.auth.logged_in`` - ``true/false``, indicates if the user was logged in when
      starting the submission.
    - ``openforms.auth.plugin`` - if logged in, the ID of the plugin that the user was logged in
      with.

``openforms.submission.completions``
    Counts the number of form submissions completed by end-users. Additional attributes
    are:

    - ``openforms.form.uuid`` - the unique database ID of the form.
    - ``openforms.form.name`` - the name of the form that was submitted.

``openforms.submission.suspensions``
    Counts the number of submissions suspended/paused by end-users. Additional
    attributes are:

    - ``openforms.form.uuid`` - the unique database ID of the form.
    - ``openforms.form.name`` - the name of the form that was submitted.

``openforms.submission.step_saves``
    Counts the number times a submission step is saved (i.e. the user submits and goes
    to the next step). Additional attributes are:

    - ``openforms.step.name`` - the name of the step that was saved.
    - ``openforms.step.number`` - the step sequence, starting at 1 for the first step.
    - ``openforms.form.uuid`` - the unique database ID of the form.
    - ``openforms.form.name`` - the name of the form that was submitted.
    - ``type`` - ``create`` or ``update``. Users can go back to a step and modify
      details, which results in an update.

``openforms.submission_count``
    The total count of submissions in the database. This is a global metric, you must
    take care in de-duplicating results. Additional attributes are:

    - ``scope`` - fixed, set to ``global`` to enable de-duplication.
    - ``openforms.openforms.form.name`` - the name of the form that the submission belongs to.
    - ``type`` - the kind of submission, possible values are ``successful``,
      ``incomplete``, ``errored``,  ``other`` which maps to the associated retention
      periods.

    Sample PromQL query, to report the submissios per stage and form:

    .. code-block:: promql

        max by (type, form_name) (
          last_over_time(
            otel_submissions_count{scope="global"}
            [5m]
          )
        )

``openforms.attachment_upload.file_size``
    A histogram of submission attachments, with buckets covering file upload sizes from
    0 bytes to 1 GiB (Open Forms by default limits uploads to 50 MB). Additional
    attributes are:

    - ``openforms.step.name`` - the name of the step that was saved.
    - ``openforms.step.number`` - the step sequence, starting at 1 for the first step.
    - ``openforms.form.uuid`` - the unique database ID of the form.
    - ``openforms.form.name`` - the name of the form that was submitted.
    - ``content_type`` - the file type of the attachment.

``openforms.submission.attachments_per_submission``
    A histogram counting the amount of attachments within a submission. Additional
    attributes are:

    - ``openforms.form.uuid`` - the unique database ID of the form.
    - ``openforms.form.name`` - the name of the form that was submitted.

Plugins
-------

``openforms.plugin.usage_count``
    A gauge reporting how many times each (installed) plugin is used in an instance.
    This is a global metric, you must take care in de-duplicating results. Additional
    attributes are:

    - ``scope`` - fixed, set to ``global`` to enable de-duplication.
    - ``openforms.plugin.module`` - the feature module the plugin/metric belongs to, such as
      ``registrations``, ``prefill``, ``authentication``...
    - ``openforms.plugin.identifier`` - the unique identifier for a plugin. The combination of
      ``(module, identifier)`` is guaranteed to be unique.
    - ``openforms.plugin.is_enabled`` - flag to indicate whether the plugin is enabled or not.
      Disabled plugin metrics should have a value of ``0`` during normal operation.
    - ``openforms.plugin.is_demo`` - flag that marks demo plugins only available for testing.
