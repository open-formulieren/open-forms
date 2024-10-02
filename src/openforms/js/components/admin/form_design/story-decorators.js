import {FeatureFlagsContext, FormContext} from 'components/admin/form_design/Context';
import {ValidationErrorsProvider} from 'components/admin/forms/ValidationErrors';

import {FormLogicContext} from './Context';

export const FeatureFlagsDecorator = (Story, {parameters}) => (
  <FeatureFlagsContext.Provider
    value={{
      ZGW_APIS_INCLUDE_DRAFTS: parameters?.featureFlags?.ZGW_APIS_INCLUDE_DRAFTS ?? false,
      REGISTRATION_OBJECTS_API_ENABLE_EXISTING_OBJECT_INTEGRATION:
        parameters?.featureFlags?.REGISTRATION_OBJECTS_API_ENABLE_EXISTING_OBJECT_INTEGRATION ??
        false,
    }}
  >
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
      form: args.form || {},
      formSteps: args.availableFormSteps || [],
      staticVariables: args.availableStaticVariables || [],
      formVariables: args.availableFormVariables || [],
      registrationPluginsVariables: args.registrationPluginsVariables || [],
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

export const ValidationErrorsDecorator = (Story, {args, parameters}) => (
  <ValidationErrorsProvider errors={args.validationErrors ?? parameters.validationErrors ?? []}>
    <Story />
  </ValidationErrorsProvider>
);
