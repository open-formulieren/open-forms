import {Form, Formik} from 'formik';
import {Fragment, useEffect} from 'react';
import {fn} from 'storybook/test';

import {
  FeatureFlagsContext,
  FormContext,
  TinyMceContext,
} from 'components/admin/form_design/Context';
import Fieldset from 'components/admin/forms/Fieldset';
import {ReactSelectContext} from 'components/admin/forms/ReactSelect';
import {ValidationErrorsProvider} from 'components/admin/forms/ValidationErrors';
import {ModalContext} from 'components/admin/modals';

import {FormLogicContext} from './Context';

export const FeatureFlagsDecorator = (Story, {parameters}) => (
  <FeatureFlagsContext.Provider
    value={{
      ZGW_APIS_INCLUDE_DRAFTS: parameters?.featureFlags?.ZGW_APIS_INCLUDE_DRAFTS ?? false,
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

// provide necessary django elements to get the right styling
export const AdminChangeFormDecorator = (Story, {parameters}) => {
  const Wrapper = parameters?.adminChangeForm?.wrapFieldset ? Fieldset : Fragment;
  return (
    <form>
      <Wrapper>
        <Story />
      </Wrapper>
    </form>
  );
};

/**
 * Decorator to mark story as being rendered inside a modal.
 *
 * It ensures that the DOM layout/hierarchy is as expected w/r to styling effects.
 */
export const FormModalContentDecorator = Story => {
  // // remove the change-form body class which affects the positioning of validation errors
  // useEffect(() => {
  //   // body of the story inside the story iframe
  //   const body = document.querySelector('body');
  //   body.classList.remove('change-form');
  // }, []);
  return (
    <div className="react-modal">
      <div className="react-modal__form">
        <Story />
      </div>
    </div>
  );
};

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
        selectedAuthPlugins: args.selectedAuthPlugins || [],
      },
      components: args.availableComponents || {},
      registrationBackends: args.registrationBackends || [],
      languages: [
        {
          code: 'nl',
          label: 'Nederlands',
        },
        {
          code: 'en',
          label: 'Engels',
        },
      ],
      translationEnabled: false,
      newLogicEvaluationEnabled: args.newLogicEvaluationEnabled || false,
    }}
  >
    <Story />
  </FormContext.Provider>
);

export const TinyMceDecorator = Story => (
  <TinyMceContext.Provider value="static/tinymce/tinymce.min.js">
    <Story />
  </TinyMceContext.Provider>
);

export const ValidationErrorsDecorator = (Story, {args, parameters}) => (
  <ValidationErrorsProvider errors={args.validationErrors ?? parameters.validationErrors ?? []}>
    <Story />
  </ValidationErrorsProvider>
);

/**
 * Wrap the story in a Formik component, which provides the necessary context.
 *
 * Formik props can be provided via `parameters.formik`.
 */
export const FormikDecorator = (Story, context) => {
  const isDisabled = context.parameters?.formik?.disable ?? false;
  if (isDisabled) {
    return <Story />;
  }
  const initialValues = context.parameters?.formik?.initialValues || {};
  const initialErrors = context.parameters?.formik?.initialErrors || {};
  const initialTouched = context.parameters?.formik?.initialTouched || {};
  const wrapForm = context.parameters?.formik?.wrapForm ?? true;
  const onSubmit = context.parameters?.formik?.onSubmit ?? fn();
  return (
    <Formik
      initialValues={initialValues}
      initialErrors={initialErrors}
      initialTouched={initialTouched}
      enableReinitialize
      onSubmit={onSubmit}
    >
      {wrapForm ? (
        <Form data-testid="story-form">
          <Story />
        </Form>
      ) : (
        <Story />
      )}
    </Formik>
  );
};

export const withModalDecorator = Story => (
  <ModalContext.Provider
    value={{
      // only for storybook integration, do not use this in real apps!
      parentSelector: () => document.getElementById('storybook-root'),
      ariaHideApp: false,
    }}
  >
    <Story />
  </ModalContext.Provider>
);

export const withReactSelectDecorator = Story => (
  <ReactSelectContext.Provider
    value={{
      // only for storybook integration, do not use this in real apps!
      parentSelector: () => document.getElementById('storybook-root'),
    }}
  >
    <Story />
  </ReactSelectContext.Provider>
);
