from digid_eherkenning.models.digid import DigidConfiguration
from digid_eherkenning.models.eherkenning import EherkenningConfiguration

ADDITIONAL_CSP_VALUES = {
    "digid": "https://digid.nl https://*.digid.nl",
    "eherkenning": "",
}

CONFIG_TYPES = {
    DigidConfiguration: "digid",
    EherkenningConfiguration: "eherkenning",
}
