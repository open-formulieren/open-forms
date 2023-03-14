import {FormContext} from 'components/admin/form_design/Context';

import {FormLogicContext} from './Context';

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
    }}
  >
    <Story />
  </FormContext.Provider>
);
