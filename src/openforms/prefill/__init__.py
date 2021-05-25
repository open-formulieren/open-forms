"""
This package holds the base module structure for the pre-fill plugins used in Open Forms.

Various sources exist that can be consulted to fetch data for an active session,
where the BSN, CoC number... can be used to retrieve this data. Think of pre-filling
the address details of a person after logging in with DigiD.

The package integrates with the form builder such that it's possible for every form
field to select which pre-fill plugin to use and which value to use from the fetched
result. Plugins can be registered using a similar approach to the registrations
package. Each plugin is responsible for exposing which attributes/data fragments are
available, and for performing the actual look-up. Plugins receive the
:class:`openforms.submissions.models.Submission` instance that represents the current
form session of an end-user.

Pre-fill values are embedded as default values for form fields, dynamically for every
user session using the component rewrite functionality in
:module:`openforms.forms.custom_field_types`.

So, to recap:

1. Plugins are defined and registered
2. When editing form definitions in the admin, content editors can opt-in to pre-fill
   functionality. They select the desired plugin, and then the desired attribute from
   that plugin.
3. End-user starts the form and logs in, thereby creating a session/``Submission``
4. The submission-specific form definition configuration is enhanced with the pre-filled
   form field default values.
"""
from typing import TYPE_CHECKING, Dict, List, Union

from zgw_consumers.concurrent import parallel

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


JSONPrimitive = Union[str, int, None, float]
JSONValue = Union[JSONPrimitive, "JSONObject", List["JSONValue"]]
JSONObject = Dict[str, JSONValue]


def apply_prefill(configuration: JSONObject, submission: "Submission", register=None):
    """
    Takes a Formiojs definition and invokes all the pre-fill plugins.

    The entire form definition is parsed, plugins and their attributes are extracted
    and each plugin is invoked with the list of attributes (in parallel).
    """
    from .registry import register as default_register

    register = register or default_register

    with parallel() as executor:
        ...

    return configuration  # TODO
