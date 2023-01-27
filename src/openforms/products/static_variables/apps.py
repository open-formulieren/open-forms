from django.apps import AppConfig


class ProductStaticVariables(AppConfig):
    name = "openforms.products.static_variables"
    label = "products_static_variables"
    verbose_name = "Products static variables"

    def ready(self):
        from . import static_variables  # noqa
