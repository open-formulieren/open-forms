from __future__ import annotations

from datetime import date

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from dateutil.relativedelta import relativedelta
from tablib import Dataset

from ..models import Form
from ..statistics import export_registration_statistics


def get_first_of_previous_month() -> date:
    now = timezone.localtime()
    one_month_ago = now - relativedelta(months=1)
    first_of_previous_month = one_month_ago.replace(day=1)
    return first_of_previous_month.date()


def get_last_of_previous_month() -> date:
    now = timezone.localtime()
    first_of_current_month = now.replace(day=1)
    get_last_of_previous_month = first_of_current_month - relativedelta(days=1)
    return get_last_of_previous_month.date()


class ExportStatisticsForm(forms.Form):
    start_date = forms.DateField(
        label=_("From"),
        required=True,
        initial=get_first_of_previous_month,
        help_text=_(
            "Export form submission that were submitted on or after this date."
        ),
        widget=AdminDateWidget,
    )
    end_date = forms.DateField(
        label=_("Until"),
        required=True,
        initial=get_last_of_previous_month,
        help_text=_(
            "Export form submission that were submitted before or on this date."
        ),
        widget=AdminDateWidget,
    )
    limit_to_forms = forms.ModelMultipleChoiceField(
        label=_("Forms"),
        required=False,
        queryset=Form.objects.filter(_is_deleted=False),
        help_text=_(
            "Limit the export to the selected forms, if specified. Leave the field "
            "empty to export all forms. Hold CTRL (or COMMAND on Mac) to select "
            "multiple options."
        ),
    )

    def export(self) -> Dataset:
        start_date: date = self.cleaned_data["start_date"]
        end_date: date = self.cleaned_data["end_date"]
        return export_registration_statistics(
            start_date,
            end_date,
            self.cleaned_data["limit_to_forms"],
        )
