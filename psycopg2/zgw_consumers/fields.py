from itertools import groupby

from django import forms
from django.contrib.admin import widgets

from .service import get_informatieobjecttypen


def get_iot_choices():
    iots = get_informatieobjecttypen()
    iots = sorted(iots, key=lambda iot: (iot.catalogus.domein, iot.catalogus.rsin))

    for catalogus, _iots in groupby(iots, key=lambda iot: iot.catalogus):
        group = f"{catalogus.domein} - {catalogus.rsin}"
        iot_choices = [(iot.url, iot.omschrijving) for iot in _iots]
        yield (group, iot_choices)


class InformatieObjectTypeField(forms.ChoiceField):
    widget = widgets.AdminRadioSelect

    def __init__(self, choices=get_iot_choices, *args, **kwargs):
        super().__init__(choices=choices, *args, **kwargs)
