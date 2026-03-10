#!/usr/bin/env python
from __future__ import annotations

import sys
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

import django
from django.db.models import BigIntegerField, F, OuterRef, Subquery
from django.db.models.functions import Cast

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


DAY_IN_SECONDS = 60 * 60 * 24
SAFE_TRESHOLD_SECONDS = 60 * 15  # within 15 minutes -> likely legitimate

type Row = tuple[int | str, str, str | float, str]


def report_submissions_accessed(report_all_accesses: bool = False) -> None:
    from django.contrib.contenttypes.models import ContentType

    from openforms.logging.models import TimelineLogProxy
    from openforms.submissions.models import Submission

    content_type = ContentType.objects.get_for_model(Submission)

    completed_earlier = (
        TimelineLogProxy.objects.filter(
            content_type=content_type,
            extra_data__log_event="form_submit_success",
            object_id=OuterRef("object_id"),
            timestamp__lt=OuterRef("timestamp"),
        )
        .order_by("-timestamp")
        .values("timestamp")[:1]
    )

    accesses_after_completion = (
        TimelineLogProxy.objects.annotate(
            submission_id=Cast("object_id", output_field=BigIntegerField()),
            submission_completed_at=Subquery(completed_earlier),
            delta=F("timestamp") - F("submission_completed_at"),
        )
        .filter(
            extra_data__log_event="submission_details_view_api",
            submission_completed_at__isnull=False,
        )
        .order_by("submission_id")
    )

    submissions: dict[int, Submission] = Submission.objects.filter(
        pk__in=accesses_after_completion.values_list("submission_id", flat=True)
    ).in_bulk()

    def _emit_rows(log_items) -> Iterator[Row]:
        if not log_items:
            return

        # all items are about the same submission
        sub_id = log_items[0].submission_id
        submission = submissions.get(sub_id)

        # check if it was cosigned within 15 mins of being accessed - while this is not
        # a 100% guarantee that the cosigner is the intended one, it should raise flags
        # in downstream systems due to an unexpected BSN (KVK) being used in the cosign.
        if (
            submission is not None
            and not report_all_accesses
            and (state := submission.cosign_state).is_signed
            and (cosigned_on_timestamp := state.signing_details.get("cosign_date"))
            and (cosigned_on := datetime.fromisoformat(cosigned_on_timestamp))
            and len(log_items) == 1
        ):
            time_between_cosign_and_retrieve = cosigned_on - log_items[0].timestamp
            if time_between_cosign_and_retrieve <= timedelta(
                seconds=SAFE_TRESHOLD_SECONDS
            ):
                return

        # treat everything else as suspicious
        yield ("--------", "", "", "")
        for log_item in log_items:
            delta_seconds = log_item.delta.total_seconds()
            time_since: str
            if delta_seconds < 60:  # less than a minute
                time_since = "< 1 min"
            elif (
                60 <= delta_seconds < 60 * 30
            ):  # between 1 - 30 mins - considered not suspicious
                time_since = f"{int(delta_seconds // 60)} min"
            elif delta_seconds < DAY_IN_SECONDS:
                time_since = f"(!) {int(delta_seconds // (60 * 60))} hours"
            elif delta_seconds < DAY_IN_SECONDS * 7:
                time_since = f"(!) {int(delta_seconds // (DAY_IN_SECONDS))} days"
            else:
                time_since = f"(!) {int(delta_seconds // (DAY_IN_SECONDS * 7))} weeks"

            yield (
                log_item.submission_id,
                submission.public_registration_reference if submission else "-",
                time_since,
                log_item.timestamp.isoformat(),
            )

    def _gen_data() -> Iterator[Row]:
        prev_id: int = 0
        _accesses: list[TimelineLogProxy] = []

        for log_item in accesses_after_completion.iterator():
            sub_id = log_item.submission_id
            if sub_id != prev_id:
                prev_id = sub_id
                yield from _emit_rows(_accesses)
                # reset
                _accesses = []
            _accesses.append(log_item)

        yield from _emit_rows(_accesses)

    click.echo("Submissions that were accessed after completion:")
    click.echo(
        tabulate(
            _gen_data(),
            headers=(
                "Submission ID",
                "Submission reference",
                "Accessed after (since completion)",
                "Access timestamp",
            ),
        )
    )


def main(skip_setup=False, report_all_accesses: bool = False) -> None:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    report_submissions_accessed(report_all_accesses)


@click.command()
@click.option(
    "--report-all-accesses",
    is_flag=True,
    default=False,
    help="Report all accesses, including what looks like legitimate cosigning",
)
def cli(report_all_accesses):
    main(skip_setup=False, report_all_accesses=report_all_accesses)


if __name__ == "__main__":
    cli()
