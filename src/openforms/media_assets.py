from django.forms import Media, Script

from django_vite.core.asset_loader import DjangoViteAssetLoader


def get_custom_assets(*, include_bootstrap: bool = False):
    # tap into django-vite internals to automatically switch between dev & prod mode
    vite = DjangoViteAssetLoader.instance()

    css: list[str] = [vite.generate_vite_asset_url("src/openforms/scss/screen.scss")]
    if include_bootstrap:
        css.insert(
            0,
            "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css",
        )

    return Media(
        css={"all": css},
        js=(  # pyright: ignore[reportArgumentType]
            Script(
                vite.generate_vite_asset_url("src/openforms/js/index.js"),
                type="module",
            ),
        ),
    )
