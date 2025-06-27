"""
Provide a (SOAP) client for StUF-ZDS 1.2 services.

This package specializes in StUF-ZDS 1.2 interaction to create and update "Zaken" via
the StUF-standard.

**Testing**

Testing the messages we send for correctness is notoriously challenging. There are no
known reference implementations or test instances that we can talk to to validate the
correct behaviour.

Additionally, while can use XSD-validation for StUF-BG, this doesn't work for StUF-ZDS
as the published validation schemas are broken. The root schema leads to a complicated
import/include map where the same target namespace ends up being imported from different
files, which doesn't work with lxml/libxml2, as it only processes a namespace once.
This then leads to errors claiming that certain types are not defined - because the
referenced schema was skipped. Fixing these schema's is a massive undertaking and can't
be justified to waste development time there.
"""
