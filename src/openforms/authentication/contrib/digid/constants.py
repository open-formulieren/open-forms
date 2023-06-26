from digid_eherkenning.choices import DigiDAssuranceLevels as _DigiDAssuranceLevels

PLUGIN_ID = "digid"
DIGID_AUTH_SESSION_KEY = f"{PLUGIN_ID}:bsn"
DIGID_AUTH_SESSION_AUTHN_CONTEXTS = f"{PLUGIN_ID}:authn_contexts"
DIGID_DEFAULT_LOA = _DigiDAssuranceLevels.middle
