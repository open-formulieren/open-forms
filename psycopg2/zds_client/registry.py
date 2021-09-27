import logging

logger = logging.getLogger(__name__)


class ClientRegistry:
    def __init__(self):
        self._registry = {}

    def __getitem__(self, key):
        return self._registry[key]

    def __delitem__(self, key):
        del self._registry[key]

    def __setitem__(self, key, value):
        if key in self._registry:
            logger.debug("Overwriting config for '%s'", key)
        self._registry[key] = value

    def __contains__(self, key):
        return key in self._registry

    def register(self, alias: str, config: dict):
        self._registry[alias] = config


registry = ClientRegistry()
