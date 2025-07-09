from digid_eherkenning.choices import AssuranceLevels

EHERKENNING_PLUGIN_ID = "eherkenning"
EHERKENNING_AUTH_SESSION_KEY = f"{EHERKENNING_PLUGIN_ID}:kvk"
EHERKENNING_AUTH_SESSION_AUTHN_CONTEXTS = f"{EHERKENNING_PLUGIN_ID}:authn_contexts"
EHERKENNING_DEFAULT_LOA = AssuranceLevels.substantial
EIDAS_AUTH_SESSION_KEY = "eidas:pseudo"
EIDAS_AUTH_SESSION_AUTHN_CONTEXTS = "eidas:authn_contexts"
