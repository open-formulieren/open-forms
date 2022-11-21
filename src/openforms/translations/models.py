from django.db.models.base import ModelBase

from djangorestframework_camel_case.util import camel_to_underscore

from openforms.forms.models.utils import set_dynamic_literal_getters


class TranslatedLiteralsModelBase(ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        super_new = super().__new__

        new_class = super_new(cls, name, bases, attrs, **kwargs)

        set_dynamic_literal_getters(
            new_class.literal_fields,
            new_class,
            camel_to_underscore(new_class._meta.object_name)[1:],
        )
        return new_class
