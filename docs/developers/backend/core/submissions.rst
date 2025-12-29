.. _developers_backend_core_submissions:

===========================
Core: submission processing
===========================

Once a form is submitted by the user, a number of actions take place to process
this submission. The complete process is shown below.

.. image:: _assets/submission_flow.png

Depending on the plugins that are active, some actions are skipped (boxes with
the dotted borders). Some actions are blocking but most actions have a fall
through mechanism to prevent the user from waiting for feedback for too long.

Globally, the various actions and plugin categories are processed in order:

#. If applicable, an :ref:`appointment <developers_appointment_plugins>` is
   created. If this fails, the submission is blocked and the user sees an error
   message and can try again.
#. Pre-registration step. Each :ref:`registration plugin <developers_registration_plugins>` can perform
   pre-registration task, like for example generating and setting a submission reference ID. If no registration backend
   is configured, then an internal ID is generated and set on the submission.
#. Component pre-registration step. A group of tasks run in parallel for all components that implement the
   :ref:`pre-registration hook <developers_backend_core_formio_pre_registration>`. The results are processed
   after all component pre-registration tasks are completed.
#. A PDF is created that the user can download.
   This PDF is also uploaded to most
   :ref:`registration backends <developers_registration_plugins>`, depending
   on the plugin.
#. If a :ref:`registration backend <developers_registration_plugins>` is configured, the submission is registered.
#. The confirmation page is shown, containing appointment information if
   applicable and the registration or internal ID. If payment is due, a payment
   link is also shown to start the payment process.
#. If the user clicks on the payment link, the
   :ref:`payment process <developers_payment_plugins>` starts. If this process
   is not completed in a reasonable amount of time, it is assumed the user did
   not pay. If payment is completed within or after the timeout, the
   registration is updated with the payment status.
#. If no payment was required, or payment was completed, or the payment timeout
   was reached, a confirmation email is sent. Depending on all the results of
   the previous actions, the confirmation email shows different contents.

The confirmation email can show submission details, appointment details
(including links to cancel the appointment), payment details(including a link to pay if not done so already),
cosign details and custom information as part of the form.

Under the hood
--------------

The steps described above are orchestrated by :meth:`openforms.submissions.tasks.on_post_submission_event`.
This method schedules the following tasks/chains:

- Task :meth:`openforms.submissions.tasks.user_uploads.cleanup_temporary_files_for`
- A chain with the following tasks:

  - :meth:`openforms.appointments.tasks.maybe_register_appointment`
  - :meth:`openforms.registrations.tasks.pre_registration`
  - :meth:`openforms.registrations.tasks.execute_component_pre_registration_group` which runs the
    following tasks in parallel:

    - :meth:`openforms.registrations.tasks.execute_component_pre_registration`, one for each
      component implementing
      :ref:`pre-registration hook <developers_backend_core_formio_pre_registration>`

  - :meth:`openforms.registrations.tasks.process_component_pre_registration`
  - :meth:`openforms.submissions.tasks.pdf.generate_report_task`
  - :meth:`openforms.registrations.tasks.registration`
  - :meth:`openforms.payments.tasks.update_submission_payment_status`
  - :meth:`openforms.submissions.tasks.finalise_completion` which schedules the following tasks (not in a chain):

    - :meth:`openforms.submissions.tasks.schedule_emails`
    - :meth:`openforms.submissions.tasks.cleanup.maybe_hash_identifying_attributes`

The IDs of the tasks scheduled in the chain are saved in a model
:class:`openforms.submissions.models.PostCompletionMetadata` which is linked (foreign key) to the submission.
With the task IDs, we can inspect the status of the tasks and communicate the status of the chain back to the frontend,
so that the confirmation page can be shown.

Method :meth:`openforms.submissions.tasks.on_post_submission_event` is not only called upon completing a submission, but
also when the following events happen:

- Payment is completed
- Submission is cosigned
- A retry flow is triggered (either because the registration failed or because the payment status update failed).

There is a possibility that the payment and the cosign happen at the same time. Since the task
:meth:`openforms.submissions.tasks.schedule_emails` is a Celery Once task, this should not lead to two confirmation
emails being sent at the same time. Since the content of the confirmation email is deduced by the state of the submission,
even in this edge case the email body should contain the correct information.
