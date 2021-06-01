"""
The :module:`appointments` package provides the creation of appointments for submissions.

Once a form is submitted ('completed') by an end-user, a
:class:`openforms.submissions.models.Submission` instance is available holding all the
submitted data.

Sometimes an appointment has to be registered as part of this submission. This package
provides a public Python API to trigger this mechanism, where each individual plugin
implements said appropriate system.

The registered plugins all have their own specific configuration and quirks, and we
will expose this to the form designers / editors. We couple a single form object to
a particular backend that needs to handle it.

See ``doc/module_architecture.md`` for an example and the bigger picture with other
modules.
"""
