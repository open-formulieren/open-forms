import React from 'react';

const TinyMceContext = React.createContext('');
TinyMceContext.displayName = 'TinyMceContext';

const FeatureFlagsContext = React.createContext({});
FeatureFlagsContext.displayName = 'FeatureFlagsContext';

const FormContext = React.createContext({
  form: {url: '', uuid: ''},
  components: {},
  formSteps: [],
  formDefinitions: [],
  reusableFormDefinitionsLoaded: false,
  formVariables: {},
  registrationBackends: [],
  plugins: {},
  languages: [],
  translationEnabled: false,
});
FormContext.displayName = 'FormContext';

const FormLogicContext = React.createContext({
  services: [],
  serviceFetchConfigurations: [],
  onServiceFetchAdd: () => null,
});
FormLogicContext.displayName = 'FormLogicContext';

const APIContext = React.createContext({
  crsftoken: '',
});
APIContext.displayName = 'APIContext';

export {APIContext, FormContext, FormLogicContext, TinyMceContext, FeatureFlagsContext};
