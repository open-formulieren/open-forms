import React from 'react';

const TinyMceContext = React.createContext('');
TinyMceContext.displayName = 'TinyMceContext';

const FeatureFlagsContext = React.createContext({});
FeatureFlagsContext.displayName = 'FeatureFlagsContext';

const FormContext = React.createContext({
  form: {url: ''},
  components: {},
  formSteps: [],
  formDefinitions: [],
  formVariables: {},
  plugins: {},
  languages: [],
  translationEnabled: false,
});
FormContext.displayName = 'FormContext';

const FormLogicContext = React.createContext({
  services: [],
  serviceFetchConfigurations: [],
});
FormContext.displayName = 'FormLogicContext';

const APIContext = React.createContext({
  crsftoken: '',
});
APIContext.displayName = 'APIContext';

export {APIContext, FormContext, FormLogicContext, TinyMceContext, FeatureFlagsContext};
