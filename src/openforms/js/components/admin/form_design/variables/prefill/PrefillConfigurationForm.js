import {Formik} from 'formik';
import PropTypes from 'prop-types';
import {useState} from 'react';
import {FormattedMessage} from 'react-intl';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {ValidationErrorsProvider} from 'components/admin/forms/ValidationErrors';

import PluginField from './PluginField';
import PLUGIN_COMPONENT_MAPPING from './constants';

const prepareErrors = errors => {
  const allErrors = [];
  Object.entries(errors).forEach(([key, errObj]) => {
    if (!errObj) return;
    if (Array.isArray(errObj)) {
      allErrors.push(...errObj.map(err => [key, err]));
    } else {
      // FIXME: this violates the prop type of ValidationErrorsProvider :/
      allErrors.push([key, errObj]);
    }
  });
  return allErrors;
};

const PrefillConfigurationForm = ({
  onSubmit,
  plugin = '',
  attribute = '',
  identifierRole = 'main',
  // Plugins are responsible for setting up the default values, since we don't know the
  // plugin-specific shape here.
  options = {},
  errors,
}) => (
  <ValidationErrorsProvider errors={prepareErrors(errors)}>
    <Formik
      initialValues={{
        plugin,
        attribute,
        identifierRole,
        options,
      }}
      onSubmit={(values, actions) => {
        onSubmit(values);
        actions.setSubmitting(false);
      }}
    >
      {({handleSubmit, values}) => {
        const PluginFormComponent =
          PLUGIN_COMPONENT_MAPPING[values.plugin]?.component ??
          PLUGIN_COMPONENT_MAPPING.default.component;
        const ToggleCopyComponent =
          PLUGIN_COMPONENT_MAPPING[values.plugin]?.toggleCopyComponent ??
          PLUGIN_COMPONENT_MAPPING.default.toggleCopyComponent;

        const [showCopyButton, setShowCopyButton] = useState(false);

        const handleToggle = event => {
          event.preventDefault();
          setShowCopyButton(!showCopyButton);
        };

        return (
          <>
            <Fieldset extraClassName="module--spaceless">
              <FormRow>
                <Field
                  name="plugin"
                  label={
                    <FormattedMessage
                      description="Variable prefill plugin label"
                      defaultMessage="Plugin"
                    />
                  }
                >
                  <>
                    <PluginField />
                    {ToggleCopyComponent ? (
                      <div style={{marginLeft: '10px', marginTop: '5px'}}>
                        <ToggleCopyComponent handleToggle={handleToggle} />
                      </div>
                    ) : null}
                  </>
                </Field>
              </FormRow>
            </Fieldset>

            <PluginFormComponent
              {...(ToggleCopyComponent && {
                showCopyButton: showCopyButton,
                setShowCopyButton: setShowCopyButton,
              })}
            />

            <SubmitRow>
              <SubmitAction
                onClick={event => {
                  event.preventDefault();
                  handleSubmit(event);
                }}
              />
            </SubmitRow>
          </>
        );
      }}
    </Formik>
  </ValidationErrorsProvider>
);

PrefillConfigurationForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  plugin: PropTypes.string,
  attribute: PropTypes.string,
  identifierRole: PropTypes.string,
  errors: PropTypes.shape({
    plugin: PropTypes.arrayOf(PropTypes.string),
    attribute: PropTypes.arrayOf(PropTypes.string),
    identifierRole: PropTypes.arrayOf(PropTypes.string),
    options: PropTypes.object,
  }).isRequired,
};

export default PrefillConfigurationForm;
