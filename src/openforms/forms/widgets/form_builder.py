from django.forms import Script, Widget


class FormBuilderWidget(Widget):
    template_name = "forms/widgets/form_builder.html"

    class Media:
        css = {
            "all": (
                "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css",
                "bundles/core-css.css",
            ),
        }
        js = (Script("bundles/core-js.js", type="module"),)
