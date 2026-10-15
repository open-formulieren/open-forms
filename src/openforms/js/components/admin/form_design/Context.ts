import type {
  AnyComponentSchema,
  JSONObject,
  JSONValue,
  SupportedLocales,
} from '@open-formulieren/types';
import React from 'react';

// Stores the TinyMCE library URL to load
const TinyMceContext = React.createContext<string>('');
TinyMceContext.displayName = 'TinyMceContext';

// Feature flags exposed from backend to frontend
interface FeatureFlagsContextType {
  ZGW_APIS_INCLUDE_DRAFTS: boolean;
}

const FeatureFlagsContext = React.createContext<FeatureFlagsContextType>({
  ZGW_APIS_INCLUDE_DRAFTS: false,
});
FeatureFlagsContext.displayName = 'FeatureFlagsContext';

interface ButtonText {
  readonly resolved: string;
  value: string;
}

interface FormVariable {
  form: string;
  formDefinition?: string | null;
  name: string;
  key: string;
  source: 'component' | 'user_defined' | 'static';
  isSensitiveData?: boolean;
  serviceFetchConfiguration?: JSONObject | null;
  prefillPlugin?: string;
  prefillAttribute?: string;
  prefillIdentifierRole?: 'main' | 'authorizee';
  dataType:
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
  initialValue?: JSONValue;
  _id?: string;
}

// Form configuration options context - as it's being edited in the admin UI.
interface FormContextType {
  form: {
    /**
     * API resource URL to the form.
     */
    url: string;
    /**
     * Unique database identifier of the form.
     */
    uuid: string;
    type: 'regular' | 'appointment' | 'single_step';
    payment: {
      backend: string;
      options: JSONObject;
    };
    /**
     * API resource URL to the product.
     */
    product: string | null;
    authBackends: {
      backend: string;
      options: JSONObject | null;
    }[];
  };
  // Mapping keyed by the component key
  components: Record<string, AnyComponentSchema>;
  formSteps: {
    uuid: string;
    slug: string;
    formDefinition: string;
    index: number;
    literals: {
      previousText?: ButtonText;
      saveText?: ButtonText;
      nextText?: ButtonText;
    };
    url: string;
    isApplicable: boolean;
  }[];
  formDefinitions: {
    url: string;
    uuid?: string;
    name: string;
    internalName?: string;
    slug?: string;
    configuration: {components?: AnyComponentSchema[]};
    loginRequired: boolean;
    isReusable: boolean;
    translations: Record<SupportedLocales, {name?: string | null}>;
  }[];
  reusableFormDefinitionsLoaded: boolean;
  formVariables: FormVariable[];
  staticVariables: FormVariable[];
  registrationPluginsVariables: {
    pluginIdentifier: string;
    pluginVerboseName: string;
    pluginVariables: FormVariable[];
  }[];
  registrationBackends: {
    key: string;
    name: string;
    backend: string;
    options: JSONObject;
  }[];
  plugins: {
    availableAuthPlugins?: {
      id: string;
      label: string;
      providesAuth: string[];
      schema: JSONObject;
    }[];
    selectedAuthPlugins?: string[];
    availablePrefillPlugins?: {
      id: string;
      label: string;
      requiresAuth: string[];
      requiresAuthPlugin: string[];
      configurationContext: JSONObject | null;
    }[];
    availableDMNPlugins?: {
      id: string;
      label: string;
    }[];
  };
  languages: {
    code: string;
    name: string;
  }[];
  translationEnabled: boolean;
  updateComponents: (
    componentKeys: string[],
    callback: (component: AnyComponentSchema) => void
  ) => void;
}

const FormContext = React.createContext<FormContextType>({
  form: {
    url: '',
    uuid: '',
    type: 'regular',
    payment: {
      backend: '',
      options: {},
    },
    product: null,
    authBackends: [],
  },
  components: {},
  formSteps: [],
  formDefinitions: [],
  reusableFormDefinitionsLoaded: false,
  formVariables: [],
  staticVariables: [],
  registrationPluginsVariables: [],
  registrationBackends: [],
  plugins: {},
  languages: [],
  translationEnabled: false,
  updateComponents: () => {},
});
FormContext.displayName = 'FormContext';

interface ServiceFetchConfiguration {
  readonly id: number;
  name: string;
  service: string;
  readonly serviceUuid: string;
  path?: string;
  method?: 'GET' | 'POST';
  headers?: JSONObject;
  queryParams?: {[k: string]: string[]};
  body?: JSONObject | null;
  dataMappingType?: '' | 'JsonLogic' | 'jq';
  mappingExpression?: JSONValue;
  cacheTimeout?: number | null;
}

interface FormLogicContextType {
  services: {
    readonly url: string;
    uuid: string;
    slug: string;
    label: string;
    apiRoot: string;
    apiType:
      | 'ac'
      | 'nrc'
      | 'zrc'
      | 'ztc'
      | 'drc'
      | 'brc'
      | 'rc'
      | 'kic'
      | 'oc'
      | 'ic'
      | 'pc'
      | 'ptc'
      | 'vrc'
      | 'tc'
      | 'bc'
      | 'cmc'
      | 'kc'
      | 'orc';
  }[];
  serviceFetchConfigurations: ServiceFetchConfiguration[];
  onServiceFetchAdd: (variableName: string, values: ServiceFetchConfiguration) => void;
}

const FormLogicContext = React.createContext<FormLogicContextType>({
  services: [],
  serviceFetchConfigurations: [],
  onServiceFetchAdd: () => null,
});
FormLogicContext.displayName = 'FormLogicContext';

// Track necessary details to be able to make API calls.
interface APIContextType {
  csrftoken: string;
}

const APIContext = React.createContext<APIContextType>({
  csrftoken: '',
});
APIContext.displayName = 'APIContext';

export {APIContext, FormContext, FormLogicContext, TinyMceContext, FeatureFlagsContext};
