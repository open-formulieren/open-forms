import {JSONValue} from '@open-formulieren/types';

type FormVariableSource = 'component' | 'userDefined';
type ServiceFetchMethod = 'GET' | 'POST';
type DataMappingType = 'JsonLogic' | 'jq';
type PrefillIdentifierRoleEnum = 'main' | 'authorizee';
type FormVariableDataType =
  | 'string'
  | 'boolean'
  | 'object'
  | 'array'
  | 'int'
  | 'float'
  | 'datetime'
  | 'time'
  | 'date'
  | 'partners'
  | 'children'
  | 'editgrid';

interface ServiceFetchConfiguration {
  readonly id: number;
  name: string;
  service: string;
  readonly serviceUuid: string;
  path?: string;
  method?: ServiceFetchMethod;
  headers?: Record<string, string>;
  queryParams?: Record<string, string[]>;
  body?: JSONValue | null;
  dataMappingType?: DataMappingType | '';
  mappingExpression?: JSONValue | null;
  cacheTimeout?: number | null;
}
export interface FormVariable {
  form: string;
  formDefinition?: string | null;
  name: string;
  key: string;
  source: FormVariableSource;
  serviceFetchConfiguration?: ServiceFetchConfiguration | null;
  prefillPlugin?: string;
  prefillAttribute?: string;
  prefillIdentifierRole?: PrefillIdentifierRoleEnum;
  prefillOptions?: JSONValue;
  dataType: FormVariableDataType;
  dataFormat?: string;
  isSensitiveData?: boolean;
  initialValue?: JSONValue | null;
  _id?: string;
}
