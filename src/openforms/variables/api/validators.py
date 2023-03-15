from openforms.api.validators import WrappedModelValidator

from ..models import ServiceFetchConfiguration


class WrappedSFCValidator(WrappedModelValidator[ServiceFetchConfiguration]):
    pass
