# GH-5942 changed the final payment status states. The `failed` status
# is no longer considered a final state. This allows users to retry previously failed
# payments and complete them. Payments done before this change however are not affected
# by this change, therefore this script was made.

import sys
from functools import partial
from pathlib import Path

import django

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def _get_payment_status(submission_payment) -> str:
    from onlinepayments.sdk.api_exception import ApiException

    from openforms.payments.contrib.worldline.models import WorldlineMerchant

    plugin_options = (
        submission_payment.plugin_options if submission_payment.plugin_options else {}
    )

    if not (merchant := plugin_options.get("merchant")):
        raise ValueError("No merchant found in plugin options")

    try:
        merchant = WorldlineMerchant.objects.get(pspid=merchant)
    except WorldlineMerchant.DoesNotExist as e:
        raise ValueError(f"No merchant found with pspid {merchant}") from e

    merchant_client = merchant.get_merchant_client()
    payments_client = merchant_client.payments()

    try:
        payment_response = payments_client.get_payment(
            submission_payment.provider_payment_id
        )
    except ApiException as e:
        raise ValueError("Payment was not found in the Worldline API") from e

    return payment_response.status


def _update_historically_failed_payments(dry_run: bool = False) -> bool:
    from django.db import transaction

    import structlog

    from openforms.payments.constants import PaymentStatus
    from openforms.payments.contrib.worldline.constants import (
        StatusCategory as WorldlineStatusCategory,
    )
    from openforms.payments.models import SubmissionPayment
    from openforms.submissions.constants import PostSubmissionEvents
    from openforms.submissions.tasks import on_post_submission_event

    logger = structlog.stdlib.get_logger(__name__)

    submission_payments = SubmissionPayment.objects.filter(
        status=PaymentStatus.failed, plugin_id="worldline"
    )
    changed_payments = []

    with transaction.atomic():
        for submission_payment in submission_payments:
            with structlog.contextvars.bound_contextvars(
                submission_uuid=str(submission_payment.submission.uuid),
                payment_uuid=str(submission_payment.uuid),
                public_order_id=submission_payment.public_order_id,
            ):
                try:
                    worldline_status = _get_payment_status(submission_payment)
                except ValueError as e:
                    logger.error("payment_status_retrieval_failed", exc_info=e)
                    continue

                last_status_category = WorldlineStatusCategory.from_payment_status(
                    worldline_status
                )
                last_status = WorldlineStatusCategory.to_of_status(last_status_category)

                if (
                    last_status == submission_payment.status
                    or last_status != PaymentStatus.completed
                ):
                    continue

                changed_payments.append(submission_payment)

                if dry_run:
                    continue

                submission_payment.status = last_status
                submission_payment.save()

                transaction.on_commit(
                    partial(
                        on_post_submission_event,
                        submission_payment.submission.pk,
                        PostSubmissionEvents.on_payment_complete,
                    )
                )

    if not changed_payments:
        click.echo(click.style("No changes found for existing payments.", fg="green"))
        return True

    click.echo(click.style("Payment statusses were updated.", fg="yellow"))
    click.echo("")
    click.echo(
        tabulate(
            [
                (
                    submission_payment.public_order_id,
                    submission_payment.submission.uuid,
                    submission_payment.provider_payment_id,
                )
                for submission_payment in changed_payments
            ],
            headers=(
                "Payment reference",
                "Submission UUID",
                "Provider payment ID",
            ),
        )
    )

    return False


def main(skip_setup: bool = False, dry_run: bool = False, **kwargs) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return _update_historically_failed_payments(dry_run=dry_run)


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Do not perform any changes to the payment statusses.",
)
def cli(dry_run: bool):
    return main(dry_run=dry_run)


if __name__ == "__main__":
    cli()
