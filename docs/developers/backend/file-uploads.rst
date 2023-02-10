.. _developers_backend_file_uploads:

============
File Uploads
============

Upload flow
===========

End users can upload files through the File Upload component when they fill out forms.

The following events happen during that process:

- The user adds a file to the component:

  - A ``POST`` request is made to ``/api/v1/formio/fileupload`` with the content of the file.
  - If configured, the file is scanned for viruses (more details :ref:`here<configuration_general_virus_scan>`). In case
    a virus is found, the file is not saved and the user receives an error alerting them that a virus was found in the file.
  - An instance of the :class:`openforms.submissions.models.TemporaryFileUpload` model is created.
  - The endpoint returns the url of the file ``/api/v1/submissions/files/<uuid>``, the file name and size. This information is added
    to the Formio submission step data.
  - The UUID of the :class:`openforms.submissions.models.TemporaryFileUpload` is added to the user session.
  - The content of the file is saved to the disk. The file is placed in the private media directory (configured through
    the ``PRIVATE_MEDIA_ROOT`` setting), within the ``temporary-uploads`` folder.

- The user saves the form step:

  - An instance of :class:`openforms.submissions.models.SubmissionFileAttachment` is created (with a relation to the
    :class:`openforms.submissions.models.TemporaryFileUpload`).
  - The file gets copied to the ``submission-uploads`` folder (which is also in the private media directory).

- The user completes the submission:

  - The UUID of the :class:`openforms.submissions.models.TemporaryFileUpload` is removed from the session.
  - The task ``cleanup_temporary_files_for`` deletes all :class:`openforms.submissions.models.TemporaryFileUpload`
    associated with the submission that has been completed.

.. note::

    When instances of  :class:`openforms.submissions.models.TemporaryFileUpload` and
    :class:`openforms.submissions.models.SubmissionFileAttachment` are deleted, the associated
    files are removed from the file system (thanks to the :class:`openforms.utils.files.DeleteFileFieldFilesMixin` mixin).


Periodical clean up
===================

There are Celery beat tasks that periodically clean up files:

- The task ``cleanup_unclaimed_temporary_files`` cleans up any :class:`openforms.submissions.models.TemporaryFileUpload` which is not related to a
  :class:`openforms.submissions.models.SubmissionFileAttachment`. This task runs once a day.
- The task ``delete_submissions`` deletes any successful/incomplete/errored submission that are older than a
  configured amount of time. This deletes the associated :class:`openforms.submissions.models.SubmissionFileAttachment`. This task runs once a day.
- The task ``make_sensitive_data_anonymous`` clears any sensitive data from a submission. It also deletes any
  :class:`openforms.submissions.models.SubmissionFileAttachment` related to the submission being cleaned. This task runs once a day.
