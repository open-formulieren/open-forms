import {FeatureFlagsContext, FormContext} from 'components/admin/form_design/Context';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';

import {FormLogicContext} from './Context';

export const FeatureFlagsDecorator = Story => (
  <FeatureFlagsContext.Provider value={{}}>
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
        availablePrefillPlugins: args.availablePrefillPlugins || [],
        availableDMNPlugins: args.availableDMNPlugins || [],
      },
      components: args.availableComponents || {},
      registrationBackends: args.registrationBackends || [],
    }}
  >
    <Story />
  </FormContext.Provider>
);

export const ValidationErrorsDecorator = (Story, {args}) => (
  <ValidationErrorContext.Provider value={args.validationErrors || []}>
    <Story />
  </ValidationErrorContext.Provider>
);
