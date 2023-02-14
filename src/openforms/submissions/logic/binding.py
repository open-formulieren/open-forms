import jq
from json_logic import jsonLogic

from openforms.forms.models import FormVariable
from openforms.typing import DataMapping, JSONValue
from openforms.variables.models import DataMappingTypes, ServiceFetchConfiguration


def bind(var: FormVariable, context: DataMapping) -> JSONValue:
    """Bind a value to a variable `var`

    :raises: :class:`requests.HTTPException` for internal server errors
    :raises: :class:`zds_client.client.ClientError` for HTTP 4xx status codes
    :raises: :class:`NotImplementedError` for FormVariable
    """
    fetch_config: ServiceFetchConfiguration | None

    match var:
        case FormVariable(service_fetch_configuration=fetch_config) if fetch_config:
            client = fetch_config.service.build_client()
            request_args = fetch_config.request_arguments(context)
            raw_value = client.request(**request_args)

            match fetch_config.data_mapping_type, fetch_config.mapping_expression:
                case DataMappingTypes.jq, expression:
                    # XXX raise warning if len(result) > 1 ?
                    value = jq.compile(expression).input(raw_value).first()
                case DataMappingTypes.json_logic, expression:
                    value = jsonLogic(expression, raw_value)
                case _:
                    value = raw_value
        case _:
            raise NotImplementedError()

    return value
