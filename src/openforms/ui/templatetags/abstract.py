from django.urls import NoReverseMatch, reverse


def get_config(kwargs):
    """
    Converts kwargs into a "config".
    This pops "config" from kwargs (defaults to empty dict) and applies any other key/value in kwargs to it.
    This allows for dicts to be passed to template tags via the "config" kwarg.
    :param kwargs: dict
    :return: dict
    """
    config = kwargs.pop("config", {})
    config.update(kwargs)
    return config


def get_config_from_prefix(config, prefix):
    """
    Creates a new "config" from kwargs, only for keys that start with prefix.
    Strips prefix from resulting dict keys.
    Strips leading underscore ("_") from dict keys.
    :param config: dict, possibly output from get_config().
    :param prefix: str, the prefix (without trailing underscore) to filter config on.
    :return: dict
    """
    return {
        key[len(prefix) + 1 :]: value
        for key, value in config.items()
        if key.startswith(prefix)
    }


def get_href(config, key="href", required_name=""):
    """
    Finds a "href" value, can be a url or a url name.
    Gets key (default: "href") is from config (if set) and tries to get a reverse. Returns the value directly if a
    NoReverseMatch is raised. Returns "" if key is not set in config.
    :param config: dict, possibly output from get_config().
    :param key: str, optional, the key in config to get href from. Defaults to "href".
    :param required_name: str, optional, if set, marks key in config as required, uses required_name as component name.
    :return: str
    """
    href = config.get(key, "")

    if required_name:
        href = get_required_config_value(config, key, required_name)

    if href:
        try:
            href = reverse(href)
        except NoReverseMatch:
            pass

    return href


def get_is_active(request, config, key="href"):
    """
    Returns whether href returned by get_href() given config and key is active.
    Active can be set in config or checked by get_is_active_href().
    :param request: HttpRequest
    :param config: dict, possibly output from get_config().
    :param key: str, optional, the key in config to get href from. Defaults to "href".
    :return: bool
    """
    if type(config.get("active")) is bool:
        return config.get("active")

    href = get_href(config, key)
    return get_is_active_href(request, href)


def get_is_active_href(request, href):
    """
    Returns whether path in request.path equals href.
    :param request: HttpRequest
    :param href: str, the href to check.
    :return: bool
    """
    return request.path == href


def get_required_config_value(config, key, name=""):
    """
    Gets a "required" value from a config. Raises a meaningful MissingRequiredConfigValueException if not set.
    :param config: dict, possibly output from get_config().
    :param key: str, the key in config to get value for.
    :param name: str, optional, The name of the component, used for the error message.
    :return:
    """

    class MissingRequiredConfigValueException(Exception):
        pass

    try:
        return config[key]
    except KeyError:
        message = f"Required config value for '{key}' was not found in {config}"

        if name:
            message += f" while obtaining context for {name}"

        message += "."

        raise MissingRequiredConfigValueException(message)
