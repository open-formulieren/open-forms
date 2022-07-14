from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _


class SchemaImportForm(forms.Form):
    file = forms.FileField(
        label=_("file"),
        required=True,
        help_text=_("Import json file with JSON schema to create a formulier"),
    )


class StepForm(forms.Form):
    def __init__(self, initial_key_steps: list, *args, **kwargs):
        """
        create fields 'on fly' based of list of tuples
        user can change default step value from "1" to a different one
        Note: validatiors are here but if case if user input not correct -> fix flow in view

        """
        super().__init__(*args, **kwargs)
        # initial_key_steps: [('kenteken', 1), ('reden', 1), ... ('huisnummer', 1)]
        for form_field in initial_key_steps:
            self.fields.update(
                {
                    f"{form_field[0]}": forms.IntegerField(
                        initial=f"{form_field[1]}",
                        validators=[
                            MaxValueValidator(len(initial_key_steps)),
                            MinValueValidator(1),
                        ],
                    )
                }
            )
