from django import forms


class OpenFormsRadioSelect(forms.RadioSelect):
    template_name = "of_utils/widgets/radio.html"
    option_template_name = "of_utils/widgets/radio_option.html"
