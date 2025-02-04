def transform_selectboxes_data(value: dict[str, bool] | None) -> list[str] | None:
    if value:
        return sorted([key for key, value in value.items() if value])


TRANSFORM_DATA_MAPPING = {
    "selectboxes": transform_selectboxes_data,
}
