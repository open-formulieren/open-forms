from urllib.parse import urlparse

from .auth import ClientAuth

default_ports = {"https": 443, "http": 80}


class ClientConfig:
    def __init__(
        self,
        scheme: str = "https",
        host: str = "localhost",
        port: int = None,
        auth: ClientAuth = None,
    ):
        self.scheme = scheme
        self.host = host
        self.port = port if port else default_ports[scheme]
        self.auth = auth

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.base_url)

    @classmethod
    def from_dict(cls, _config: dict) -> "ClientConfig":
        _auth = _config.pop("auth", None)
        auth = None if not _auth else ClientAuth(**_auth)
        return cls(**_config, auth=auth)

    @classmethod
    def from_url(cls, detail_url: str) -> "ClientConfig":
        parsed_url = urlparse(detail_url)

        if ":" in parsed_url.netloc:
            host, port = parsed_url.netloc.split(":")
        else:
            host, port = parsed_url.netloc, None

        # register the config
        return cls.from_dict({"scheme": parsed_url.scheme, "host": host, "port": port})

    @property
    def base_url(self) -> str:
        """
        Calculate the base URL, without the api root base path.
        """
        base = "{}://{}".format(self.scheme, self.host)

        # if it's the default ports, we don't need to be explicit
        default_port = default_ports[self.scheme]
        if self.port == default_port:
            return base

        return "{}:{}".format(base, self.port)
