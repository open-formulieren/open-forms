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
});
FormContext.displayName = 'FormContext';

export {FormContext, TinyMceContext, FeatureFlagsContext};
