from digid_eherkenning.models import DigidConfiguration, EherkenningConfiguration

ADDITIONAL_CSP_VALUES = {
    DigidConfiguration: "https://digid.nl https://*.digid.nl",
    EherkenningConfiguration: "https://*.eherkenning.nl",
}
