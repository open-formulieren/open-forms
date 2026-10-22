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
  id: number;
  name: string;
  service: string;
  serviceUuid: string;
  path: string;
  method: ServiceFetchMethod;
  headers: Record<string, string>;
  queryParams: Record<string, string>;
  body: object | Array<any> | null;
  dataMappingType: DataMappingType | '';
  mappingExpression: string | object;
  cacheTimeout: number | null;
}
interface FormVariable {
  name: string;
  key: string;
  source: FormVariableSource;
  form: string;
  formDefinition: string | null;
  serviceFetchConfiguration: ServiceFetchConfiguration | null;
  prefillPlugin: string;
  prefillAttribute: string;
  prefillIdentifierRole: PrefillIdentifierRoleEnum;
  prefillOptions: object;
  dataType: FormVariableDataType;
  dataFormat: string;
  isSensitiveData: boolean;
  initialValue: object | Array<any> | boolean | number | string;
}

interface Product {
  url: string;
  uuid: string;
  name: string;
  price: string | null;
  information: string;
  producttype: string | null;
}

type FieldChangeEvent = {
  target: {
    name: string;
    value: any;
  };
};

export {FormVariable, Product, FieldChangeEvent};
