from functools import reduce

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import BooleanField, ChoiceField
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.config.models import GlobalConfiguration
from openforms.forms.constants import SubmissionAllowedChoices


class NestedRelatedField(NestedHyperlinkedRelatedField):
    """
    Support lookups for lookup_field separated by __.
    """

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        underscored_obj_lookups = self.lookup_field.split("__")
        obj_for_lookup = reduce(getattr, [obj] + underscored_obj_lookups[:-1])

        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj_for_lookup, "pk") and obj_for_lookup.pk in (None, ""):
            return None

        # default lookup from rest_framework.relations.HyperlinkedRelatedField
        lookup_value = getattr(obj_for_lookup, underscored_obj_lookups[-1])
        kwargs = {self.lookup_url_kwarg: lookup_value}

        # multi-level lookup
        for parent_lookup_kwarg in list(self.parent_lookup_kwargs.keys()):
            underscored_lookup = self.parent_lookup_kwargs[parent_lookup_kwarg]

            # split each lookup by their __, e.g. "parent__pk" will be split into "parent" and "pk", or
            # "parent__super__pk" would be split into "parent", "super" and "pk"
            lookups = underscored_lookup.split("__")

            # use the Django ORM to lookup this value, e.g., obj.parent.pk
            lookup_value = reduce(getattr, [obj] + lookups)

            # store the lookup_name and value in kwargs, which is later passed to the reverse method
            kwargs.update({parent_lookup_kwarg: lookup_value})

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class URLRelatedField(NestedHyperlinkedRelatedField):
    """This field still checks that the URL refers to a valid model in the database, but does not
    convert the URL to an actual object."""

    def to_internal_value(self, data):
        super().to_internal_value(data)
        return data

    def get_url(self, obj, view_name, request, format):
        return obj


def check_privacy_policy_accepted(value: bool) -> None:
    config = GlobalConfiguration.get_solo()
    assert isinstance(config, GlobalConfiguration)
    privacy_policy_valid = value if config.ask_privacy_consent else True
    if not privacy_policy_valid:
        raise serializers.ValidationError(_("Privacy policy must be accepted."))


class PrivacyPolicyAcceptedField(BooleanField):
    default_validators = [check_privacy_policy_accepted]


# TODO: ideally this should be moved into a permission-check in the view rather than
# input validation, as the end-user cannot correct this 'mistake'.
class SubmissionAllowedField(ChoiceField):
    default_error_messages = {"invalid": _("Submission of this form is not allowed.")}

    def __init__(self, *args, **kwargs):
        kwargs["choices"] = SubmissionAllowedChoices.choices
        super().__init__(*args, **kwargs)

    def to_internal_value(self, form_configuration_value: SubmissionAllowedChoices):
        if form_configuration_value != SubmissionAllowedChoices.yes:
            self.fail("invalid")
        return form_configuration_value
