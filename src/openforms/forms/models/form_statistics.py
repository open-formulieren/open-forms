from django.db import models
from django.utils.formats import localize
from django.utils.translation import gettext_lazy as _


class FormStatistics(models.Model):
    form = models.OneToOneField(
        "forms.Form",
        verbose_name=_("form"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    form_name = models.CharField(
        verbose_name=_("form name"),
        max_length=150,
        help_text=_(
            "The name of the submitted form. This is saved separately in case of form deletion."
        ),
    )
    submission_count = models.PositiveIntegerField(
        verbose_name=_("Submission count"),
        default=0,
        help_text=_("The number of the submitted forms."),
    )
    first_submission = models.DateTimeField(
        verbose_name=_("first submission"),
        help_text=_("Date and time of the first submitted form."),
        auto_now_add=True,
    )
    last_submission = models.DateTimeField(
        verbose_name=_("last submission"),
        help_text=_("Date and time of the last submitted form."),
    )

    class Meta:
        verbose_name = _("form statistics")
        verbose_name_plural = _("form statistics")

    def __str__(self):
        return _("{form_name} last submitted on {last_submitted}").format(
            form_name=self.form_name, last_submitted=localize(self.last_submission)
        )
