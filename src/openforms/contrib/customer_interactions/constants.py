from collections.abc import Mapping

from openklant_client.types.resources.digitaal_adres import SoortDigitaalAdres

from openforms.formio.typing.custom import SupportedChannels

ADDRESS_TYPES_TO_CHANNELS: Mapping[SoortDigitaalAdres, SupportedChannels] = {
    "email": "email",
    "telefoonnummer": "phoneNumber",
}
