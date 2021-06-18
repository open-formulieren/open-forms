def get_flattened_components(components):
    flattened_components = []

    for component in components:
        flattened_components.append(component)
        if nested_components := component.get("components"):
            flattened_components += get_flattened_components(nested_components)

    return flattened_components
