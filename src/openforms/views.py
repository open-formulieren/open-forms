from django.views.generic import TemplateView


class SPADemoView(TemplateView):
    template_name = "spa/build/index.html"
