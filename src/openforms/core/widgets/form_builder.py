from django.forms import Widget


class FormBuilderWidget(Widget):
    template_name = 'core/widgets/form_builder.html'

    class Media:
        css = {
            'all': (
                # 'bundles/openforms-css.css',
                'bundles/core-css.css',
            ),
        }
        js = ('bundles/core-js.js',)
