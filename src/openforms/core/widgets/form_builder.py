from django.forms import Widget


class FormBuilderWidget(Widget):
    template_name = 'core/widgets/form_builder.html'

    class Media:
        css = {
            'all': (
                'bundles/openforms-css.css',
                'https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css'
            ),
        }
        js = ('bundles/openforms-js.js',)
