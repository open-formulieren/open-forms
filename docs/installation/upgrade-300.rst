.. _installation_upgrade_300:

===================================
Upgrade details to Open Forms 3.0.0
===================================

Backwards compatibility in form import changes
==============================================

Removal of Object API object type convertion
--------------------------------------------

With the UX changes of OF 2.8.0, the Object Api registration no longer lets you use
hyperlinks when configuring the object type. The usage of hyperlinks for the object type
is now also disallowed when importing a form.

Previously the hyperlinks would be converted to the expected format, and saved as such.
The convertion will no-longer take place, and the 'to be imported' form is expected to
use the new UUID format for the object type.
