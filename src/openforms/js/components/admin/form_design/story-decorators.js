import {FeatureFlagsContext, FormContext} from 'components/admin/form_design/Context';

import {FormLogicContext} from './Context';

export const FeatureFlagsDecorator = Story => (
  <FeatureFlagsContext.Provider value={{of_service_fetch_enabled: true}}>
    <Story />
  </FeatureFlagsContext.Provider>
);

export const FormLogicDecorator = (Story, {args}) => (
  <FormLogicContext.Provider
    value={{
      services: args.availableServices || [],
      serviceFetchConfigurations: args.serviceFetchConfigurations || [],
    }}
  >
    <Story />
  </FormLogicContext.Provider>
);

export const FormDecorator = (Story, {args}) => (
  <FormContext.Provider
    value={{
      formSteps: args.availableFormSteps || [],
      staticVariables: args.availableStaticVariables || [],
      formVariables: args.availableFormVariables || [],
      selectedAuthPlugins: args.selectedAuthPlugins || [],
      plugins: {
        availableAuthPlugins: args.availableAuthPlugins || [],
      },
      components: args.availableComponents || {},
    }}
  >
    <Story />
  </FormContext.Provider>
);
