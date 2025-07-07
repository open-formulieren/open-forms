"""
Django model field integration to wrap WYSIWYG library fields.
"""

from django.db.models import TextField


class proxy:
    """
    Proxy whatever attribute to underlying base_field.
    """

    def __set_name__(self, owner, name: str):
        self.attr_name = name

    def __get__(self, field, objtype=None):
        return getattr(field.base_field, self.attr_name)

    def __set__(self, field, value):  # pragma: nocover
        setattr(field.base_field, self.attr_name, value)


class CSPPostProcessedWYSIWYGField(TextField):
    """
    A wrapper field around your WYSIWYG django field of choice.

    This is mostly used for automatic DRF serializer field introspection to apply
    the CSP post processing during serialization.

    .. todo:: Add support for native use in templates and automatic post-processing
    """

    def __init__(self, base_field, **kwargs):
        self.base_field = base_field
        # copy the base field args/kwargs to the wrapper field
        _, _, _, field_kwargs = base_field.deconstruct()
        kwargs.update(field_kwargs)
        super().__init__(**kwargs)

    @property
    def model(self):
        try:
            return self.__dict__["model"]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute 'model'"
            )

    @model.setter
    def model(self, model):
        self.__dict__["model"] = model
        self.base_field.model = model

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.base_field.set_attributes_from_name(name)

    description = proxy()
    db_type = proxy()
    get_internal_type = proxy()
    get_prep_value = proxy()

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.update(
            {
                "base_field": self.base_field.clone(),
            }
        )
        return name, path, args, kwargs

    to_python = proxy()
    formfield = proxy()
