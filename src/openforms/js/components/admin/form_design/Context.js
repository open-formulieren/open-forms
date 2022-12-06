import React from 'react';

const TinyMceContext = React.createContext('');
TinyMceContext.displayName = 'TinyMceContext';

const FeatureFlagsContext = React.createContext({});
FeatureFlagsContext.displayName = 'FeatureFlagsContext';

const FormStepContext = React.createContext({
  componentTranslations: {},
});
FormStepContext.displayName = 'FormStepContext';

const FormContext = React.createContext({
  form: {url: ''},
  components: {},
  formSteps: [],
  formDefinitions: [],
  formVariables: {},
  plugins: {},
  languages: [],
});
FormContext.displayName = 'FormContext';

export {FormContext, TinyMceContext, FeatureFlagsContext, FormStepContext};
