import uuid
from copy import deepcopy

from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _

from frozendict import frozendict

from openforms.formio.service import FormioData
from openforms.forms.models import FormDefinition, FormStep


def _make_frozen(obj):
    if not isinstance(obj, dict | list):
        return obj

    elif isinstance(obj, list):
        return tuple([_make_frozen(item) for item in obj])

    retval = frozendict()
    for key, value in obj.items():
        if isinstance(value, dict):
            frozen_value = _make_frozen(value)
        elif isinstance(value, list):
            frozen_value = tuple([_make_frozen(item) for item in value])
        else:
            frozen_value = value
        retval = retval.set(key, frozen_value)
    return retval


def _make_unfrozen(obj):
    if isinstance(obj, frozendict):
        return {key: _make_unfrozen(value) for key, value in obj.items()}

    elif isinstance(obj, tuple):
        return [_make_unfrozen(item) for item in obj]

    return obj


# Note that this exists because of data loss bug #2135 - when a FormStep is being
# deleted in the form designer (or during import/export), we do not want to destroy
# the submitted data for that step.
#
# This implements a bandaid fix where we record just enough information to reconstruct
# the FormStep in memory.
def RECORD_HISTORICAL_FORM_STEP(collector, field, sub_objs, using):
    form_steps = list(collector.data[FormStep])

    # our own reference can become NULL, since we're copying the data to our history
    # field below
    collector.add_field_update(field, None, sub_objs)

    history_field = SubmissionStep._meta.get_field("form_step_history")
    for submission_step in sub_objs:
        form_step = submission_step.form_step
        assert form_step in form_steps

        serialized_form_definition = serializers.serialize(
            "python", [form_step.form_definition]
        )[0]
        serialized_form_step = serializers.serialize("python", [form_step])[0]

        # update the history field
        frozen_history = _make_frozen(
            {
                "form_step": serialized_form_step,
                "form_definition": serialized_form_definition,
            }
        )
        collector.add_field_update(history_field, frozen_history, [submission_step])


class FrozenDjangoJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, frozendict):
            unfrozen = _make_unfrozen(o)
            return unfrozen
        return super().default(o)


class SubmissionStep(models.Model):
    """
    Submission data.

    TODO: This model (and therefore API) allows for the same form step to be
    submitted multiple times. Can be useful for retrieving historical data or
    changes made during filling out the form... but...
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    submission = models.ForeignKey("submissions.Submission", on_delete=models.CASCADE)
    form_step = models.ForeignKey(
        "forms.FormStep",
        on_delete=RECORD_HISTORICAL_FORM_STEP,
        null=True,
        blank=True,
    )
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    modified = models.DateTimeField(_("modified on"), auto_now=True)

    # bugfix for #2135
    form_step_history = models.JSONField(
        _("form step (historical)"),
        encoder=FrozenDjangoJSONEncoder,
        editable=False,
        default=None,
        blank=True,
        null=True,
    )

    # can be modified by logic evaluations/checks
    _can_submit = True
    _is_applicable: bool | None = None

    _unsaved_data = None

    class Meta:
        verbose_name = _("Submission step")
        verbose_name_plural = _("Submission steps")
        unique_together = (("submission", "form_step"),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # See #2632, and a long story here on what happens:
        #
        # When the Submission queryset is deleted, this happens through the
        # django.db.models.deletion.Collector which takes care of finding all related
        # objects to manage the cascade delete.
        #
        # It does this (apparently) in an optimized way where only the primary keys of
        # records (SubmssionStep in this case) are being loaded (via
        # ``get_candidate_relations_to_delete`` and Collector.related_objects). The
        # details are not exactly clear, but it *appears* that the form_step_id
        # field/description is deferred. This means that when you *access* this field,
        # Django will actually perform a separate query to load the (full) record with
        # the additional information from the database row, which in turn leads to a new
        # instance of the model being created, which in turn causes the __init__ method
        # to be called again and that cycle then repeats (since that field is probably
        # again deferred?).
        #
        # We can check if the field was loaded or not by checking in self.__dict__. Note
        # that this is far from public API and a structural fix is still recommended.
        if "form_step_id" in self.__dict__:
            # load the form step from historical data if the FK has been broken (due to a
            # deleted form step in the form designer/import functionality)
            if not self.form_step_id:
                self.form_step = self._load_form_step_from_history()

    def _load_form_step_from_history(self):
        history = deepcopy(self.form_step_history)

        if not history:
            return None

        # check if the form definition still exists
        fd_exists = FormDefinition.objects.filter(
            pk=history["form_definition"]["pk"]
        ).exists()
        if not fd_exists:
            del history["form_step"]["fields"]["form_definition"]

        form_step = next(
            serializers.deserialize("python", [history["form_step"]])
        ).object

        if not fd_exists:
            form_definition = next(
                serializers.deserialize("python", [history["form_definition"]])
            ).object
            form_step.form_definition = form_definition

        return form_step

    @property
    def completed(self) -> bool:
        # TODO: should check that all the data for the form definition is present?
        # and validates?
        # For now - if it's been saved, we assume that was because it was completed
        return bool(self.pk and self.data is not None)

    @property
    def can_submit(self) -> bool:
        return self._can_submit

    @property
    def is_applicable(self) -> bool:
        if self._is_applicable is not None:
            return self._is_applicable
        return self.form_step.is_applicable

    @is_applicable.setter
    def is_applicable(self, value: bool) -> None:
        self._is_applicable = value

    def reset(self):
        self.data = FormioData()
        self.save()

    @property
    def data(self) -> FormioData:
        values_state = self.submission.load_submission_value_variables_state()
        step_data = values_state.get_data(self)
        if self._unsaved_data:
            step_data.update(self._unsaved_data)
        return step_data

    @data.setter
    def data(self, data: FormioData | None) -> None:
        if isinstance(data, DirtyData):
            self._unsaved_data = data
        else:
            from .submission_value_variable import SubmissionValueVariable

            SubmissionValueVariable.objects.bulk_create_or_update_from_data(
                data, self.submission, self, update_missing_variables=True
            )


class DirtyData(FormioData):
    pass
