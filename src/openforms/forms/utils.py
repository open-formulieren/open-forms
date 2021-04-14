import uuid
from copy import deepcopy


def copy_form(instance):
    copied_form = deepcopy(instance)
    copied_form.pk = None
    copied_form.uuid = uuid.uuid4()
    copied_form.name = f"{copied_form.name} (kopie)"
    copied_form.slug = f"{copied_form.slug}-kopie"

    # TODO copy product as well?
    copied_form.product = None

    copied_form.save()

    for form_step in instance.formstep_set.all():
        copied_form_definition = deepcopy(form_step.form_definition)
        copied_form_definition.pk = None
        copied_form_definition.uuid = uuid.uuid4()
        copied_form_definition.name = f"{form_step.form_definition.name} (kopie)"
        copied_form_definition.slug = f"{form_step.form_definition.slug}-kopie"
        copied_form_definition.save()

        copied_step = deepcopy(form_step)
        copied_step.pk = None
        copied_step.uuid = uuid.uuid4()
        copied_step.form = copied_form
        copied_step.form_definition = copied_form_definition
        copied_step.save()

    return copied_form
