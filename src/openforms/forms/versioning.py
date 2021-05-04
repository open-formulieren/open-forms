import reversion


def register_versioned_models():
    """
    notes:

    if we use follow=() related objects will always become part of the same Revision (unless ignore_duplicates=True)

    if we use ignore_duplicates=True Revisions are less like a snapshot,
     because Versions might get hidden *even with follow=()* unless we explicitly use reversion.add_to_revision()
    """
    from .models import Form, FormDefinition, FormStep

    reversion.register(
        Form,
        fields=(
            "uuid",
            "name",
            "slug",
            "active",
            "product",
            "backend",
        ),
        follow=("formstep_set",),
    )
    reversion.register(
        FormStep,
        fields=(
            "order",  # this could be problematic with deleted/replaced objects
            "uuid",
            "form",
            "form_definition",
            "optional",
            "availability_strategy",
        ),
        follow=("form",),
    )
    reversion.register(
        FormDefinition,
        fields=(
            "uuid",
            "name",
            "slug",
            "configuration",
            "login_required",
        ),
    )
