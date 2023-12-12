.. _configuration_general_payment_flow:

============
Payment flow
============

For forms where a payment is required, it is possible to configure when the submission should be registered.
The setting **Wait for payment to register** can be found in the admin in the **General configuration**,
under the header **Registration**.

If **Wait for payment to register** is checked, then a submission will only be sent to the registration backend when
the payment is completed. Note that if the submission should also be co-signed, then it will be registered only when
both the payment and the co-sign are completed.

If **Wait for payment to register** is NOT checked, then the submission is registered as soon as it is completed (unless
co-sign is also needed). Then, once payment is completed, the payment status will be updated in the registration backend.
This means, that for registration backends that create a zaak (StUF-ZDS and ZGW registration backends), the
status of the zaak will be updated. In the case of the email registration backend, a second email will be sent to notify
that the payment has been received. For the MSGraph backend, the ``payment_status.txt`` file will be updated to say that
the payment was received.
