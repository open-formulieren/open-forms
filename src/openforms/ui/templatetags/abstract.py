from django.urls import reverse, NoReverseMatch


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
        key[len(prefix) + 1:]: value
        for key, value in config.items()
        if key.startswith(prefix)
    }

def get_href(config, key="href"):
    """
    Finds a "href" value, can be a url or a url name.
    Gets key (default: "href") is from config (if set) and tries to get a reverse. Returns the value directly if a
    NoReverseMatch is raised. Returns "" if key is not set in config.
    :param config: dict
    :param key: str
    :return: str
    """
    href = config.get(key, "")

    if href:
        try:
            href = reverse("href")
        except NoReverseMatch:
            pass

    return href


def get_required_config_value(config, key, name=""):
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
