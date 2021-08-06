import factory

from openforms.forms.models.form import FormLogic


class FormLogicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormLogic
