from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

EXPORT_META_KEY = "_meta"


class LogicActionTypes(DjangoChoices):
    step_not_applicable = ChoiceItem(
        "step-not-applicable", _("Mark the form step as not-applicable")
    )
    disable_next = ChoiceItem("disable-next", _("Disable the next step"))
    property = ChoiceItem("property", _("Modify a component property"))
    value = ChoiceItem("value", _("Set the value of a component"))  # DEPRECATED!
    variable = ChoiceItem("variable", _("Set the value of a variable"))

    requires_component = {property.value, value.value}
    requires_variable = {variable.value}


class PropertyTypes(DjangoChoices):
    bool = ChoiceItem("bool", _("Boolean"))
    json = ChoiceItem("json", _("JSON"))


class ConfirmationEmailOptions(DjangoChoices):
    form_specific_email = ChoiceItem("form_specific_email", _("Form specific email"))
    global_email = ChoiceItem("global_email", _("Global email"))
    no_email = ChoiceItem("no_email", _("No email"))


class SubmissionAllowedChoices(DjangoChoices):
    yes = ChoiceItem("yes", _("Yes"))
    no_with_overview = ChoiceItem("no_with_overview", _("No (with overview page)"))
    no_without_overview = ChoiceItem(
        "no_without_overview", _("No (without overview page)")
    )


class FormVariableSources(DjangoChoices):
    component = ChoiceItem("component", _("Component"))
    user_defined = ChoiceItem("user_defined", _("User defined"))


class FormVariableDataTypes(DjangoChoices):
    string = ChoiceItem("string", _("String"))
    boolean = ChoiceItem("boolean", _("Boolean"))
    object = ChoiceItem("object", _("Object"))
    array = ChoiceItem("array", _("Array"))
    int = ChoiceItem("int", _("Integer"))
    float = ChoiceItem("float", _("Float"))
    datetime = ChoiceItem("datetime", _("Datetime"))
    time = ChoiceItem("time", _("Time"))


class FormVariableStaticInitialValues(DjangoChoices):
    now = ChoiceItem("now", _("Now"))
    auth_identifier = ChoiceItem("auth_identifier", "Authentication identifier")
    auth_bsn = ChoiceItem("auth_bsn", "Authentication BSN")
    auth_kvk = ChoiceItem("auth_kvk", "Authentication KvK")
    auth_pseudo = ChoiceItem("auth_pseudo", "Authentication pseudo")
