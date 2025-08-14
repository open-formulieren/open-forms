from import_export import resources

from .models import AttributeGroup


class AttributeGroupResource(resources.ModelResource):
    class Meta:
        model = AttributeGroup
        # Use uuid as identifier
        import_id_fields = ("uuid",)
        fields = ("name", "uuid", "description", "attributes")

    def dehydrate_name(self, obj: AttributeGroup) -> str:
        # Trimming whitespace
        return obj.name.strip()

    def dehydrate_description(self, obj: AttributeGroup) -> str:
        # Trimming whitespace
        return obj.description.strip()
