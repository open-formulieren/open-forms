import {FormLogicContext} from '../Context';

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
