from django.forms import Widget


class FormBuilderWidget(Widget):
    template_name = "core/widgets/form_builder.html"

    class Media:
        css = {
            "all": (
                "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css",
                "bundles/core-css.css",
            ),
        }
        js = ("bundles/core-js.js",)
