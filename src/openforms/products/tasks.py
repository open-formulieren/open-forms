import structlog

from ..contrib.open_producten.client import get_open_producten_client
from ..contrib.open_producten.types import ActuelePrijsItem
from .models import PriceOption, Product

from openforms.celery import app
from openforms.submissions.models import Submission

logger = structlog.stdlib.get_logger(__name__)


def update_product_prices(product: Product, current_price_item: ActuelePrijsItem):
    # Remove all price options, if there are no current prices
    if not current_price_item.actuele_prijs:
        PriceOption.objects.filter(product=product).delete()
        return

    # Update/create price options based on current price item
    updated_price_option_uuids = []
    for current_price_option in current_price_item.actuele_prijs.prijsopties:
        price_option, created = PriceOption.objects.get_or_create(
            product=product,
            price_option_uuid=current_price_option.uuid,
            defaults={
                "price": current_price_option.bedrag,
                "name": current_price_option.beschrijving,
            },
        )
        if not created:
            price_option.price = current_price_option.bedrag
            price_option.save()

        updated_price_option_uuids.append(current_price_option.uuid)

    # Remove stale price options
    PriceOption.objects.filter(product=product).exclude(
        price_option_uuid__in=updated_price_option_uuids
    ).delete()


@app.task(ignore_result=True)
def update_products():
    """Activate all the forms that should be activated by the specific date and time."""
    with get_open_producten_client() as client:
        client_product_types = client.get_product_types()
        for product_type in client_product_types:
            product, created = Product.objects.get_or_create(
                product_type_uuid=str(product_type.uuid),
                defaults={
                    "name": product_type.naam,
                    "information": product_type.samenvatting,
                },
            )
            current_price = client.get_current_price(product_type.uuid)

            if not created:
                logger.info("update_product_type", product_type_uuid=product_type.uuid)
                product.name = product_type.naam
                product.information = product_type.naam
                product.save()

            update_product_prices(product, current_price)


@app.task(ignore_result=True)
def create_product(submission_id: str):
    try:
        submission = Submission.objects.get(pk=submission_id)
    except Submission.DoesNotExist:
        logger.exception(
            "Exception while creating products from Open Producten",
            exc_info=exc,
        )
        return

    bsn = (
        submission.auth_info.value
        if submission.is_authenticated and submission.auth_info
        else ""
    )
    prijs = submission.data.get("")

    form = submission.form

    def get_price_option_key():
        for step in form.formstep_set.all():
            for component in step.form_definition.configuration["components"]:
                if component["type"] == "productPrice":
                    return component["key"]
        raise ValueError("Form does not have a productPrice component")

    price_option_key = get_price_option_key()

    data = submission.data
    if not data.get(price_option_key):
        return Decimal("0")

    prijs = form.product.price_options.get(
        price_option_uuid=data[price_option_key]
    ).price

    with get_open_producten_client() as client:
        client.create_product(submission.form.product, str(prijs), bsn=bsn)
