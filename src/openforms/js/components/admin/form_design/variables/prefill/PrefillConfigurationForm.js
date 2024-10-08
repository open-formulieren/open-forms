import {Formik} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import SubmitRow from 'components/admin/forms/SubmitRow';

import DefaultFields from './DefaultFields';
import ObjectsAPIFields from './ObjectsAPIFields';
import PluginField from './PluginField';

const PLUGIN_COMPONENT_MAPPING = {
  objects_api: ObjectsAPIFields,
  default: DefaultFields,
};

const PrefillConfigurationForm = ({
  onSubmit,
  plugin = '',
  attribute = '',
  identifierRole = 'main',
  // TODO: find a better way to specify this based on the selected plugin
  options = {
    objectsApiGroup: '',
    objecttype: '',
    objecttypeVersion: null,
    variablesMapping: [],
  },
  errors,
}) => {
  return (
    <Formik
      initialValues={{
        plugin,
        attribute,
        identifierRole,
        options,
      }}
      onSubmit={(values, actions) => {
        // TODO should be implemented in https://github.com/open-formulieren/open-forms/issues/4693
        console.log(values);
        onSubmit(values);
        actions.setSubmitting(false);
      }}
    >
      {({handleSubmit, values}) => {
        const PluginFormComponent =
          PLUGIN_COMPONENT_MAPPING[values.plugin] ?? PLUGIN_COMPONENT_MAPPING.default;
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
                  errors={errors.plugin}
                >
                  <PluginField />
                </Field>
              </FormRow>
            </Fieldset>

            <PluginFormComponent errors={errors} />

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
  );
};

PrefillConfigurationForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  plugin: PropTypes.string,
  attribute: PropTypes.string,
  identifierRole: PropTypes.string,
  errors: PropTypes.shape({
    plugin: PropTypes.arrayOf(PropTypes.string),
    attribute: PropTypes.arrayOf(PropTypes.string),
    identifierRole: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
};

export default PrefillConfigurationForm;
