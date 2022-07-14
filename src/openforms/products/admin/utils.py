def get_initial_fields_steps_tupels(properties_dict: dict) -> list:
    """
    create list of tuples with fields == keys and default step ==1
    """

    fields_choices = []
    for item in properties_dict["properties"].keys():
        fields_choices.append((f"{item}", 1))

    return fields_choices


def get_initial_fields_steps_dict(properties_dict: dict) -> list:
    """
    create list of tuples with fields == keys and default step ==1
    """

    fields_choices = {}
    for item in properties_dict["properties"].keys():
        fields_choices.update({f"{item}": "1"})

    return fields_choices
