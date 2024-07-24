import {Formik, useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext, useEffect} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';
import useUpdateEffect from 'react-use/esm/useUpdateEffect';

import {FormContext} from 'components/admin/form_design/Context';
import {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import Select, {LOADING_OPTION} from 'components/admin/forms/Select';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {get} from 'utils/fetch';

import {IDENTIFIER_ROLE_CHOICES} from '../constants';

const PrefillConfigurationForm = ({
  onSubmit,
  plugin = '',
  attribute = '',
  identifierRole = 'main',
  errors,
}) => (
  // XXX: we're not using formik's initialErrors yet because it doesn't support arrays of
  // error messages, which our backend *can* produce.
  <Formik
    initialValues={{
      plugin,
      attribute,
      identifierRole,
    }}
    onSubmit={(values, actions) => {
      onSubmit(values);
      actions.setSubmitting(false);
    }}
  >
    {({handleSubmit}) => (
      <>
        <Fieldset>
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

          <FormRow>
            <Field
              name="attribute"
              label={
                <FormattedMessage
                  description="Variable prefill attribute label"
                  defaultMessage="Attribute"
                />
              }
              errors={errors.attribute}
            >
              <AttributeField />
            </Field>
          </FormRow>

          <FormRow>
            <Field
              name="identifierRole"
              label={
                <FormattedMessage
                  description="Variable prefill identifier role label"
                  defaultMessage="Identifier role"
                />
              }
              errors={errors.identifierRole}
            >
              <IdentifierRoleField />
            </Field>
          </FormRow>
        </Fieldset>

        <SubmitRow>
          <SubmitAction
            onClick={event => {
              event.preventDefault();
              handleSubmit(event);
            }}
          />
        </SubmitRow>
      </>
    )}
  </Formik>
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
  }).isRequired,
};

const PluginField = () => {
  const [fieldProps] = useField('plugin');
  const {setFieldValue} = useFormikContext();
  const {
    plugins: {availablePrefillPlugins},
  } = useContext(FormContext);

  const {value} = fieldProps;

  // reset the attribute value whenever the plugin changes
  useUpdateEffect(() => {
    setFieldValue('attribute', '');
  }, [setFieldValue, value]);

  const choices = availablePrefillPlugins.map(plugin => [plugin.id, plugin.label]);
  return <Select allowBlank choices={choices} id="id_plugin" {...fieldProps} />;
};

const AttributeField = () => {
  const [fieldProps] = useField('attribute');
  const {
    values: {plugin},
  } = useFormikContext();

  // Load the possible prefill attributes
  // XXX: this would benefit from client-side caching
  const {
    loading,
    value = [],
    error,
  } = useAsync(async () => {
    if (!plugin) return [];

    const endpoint = `/api/v2/prefill/plugins/${plugin}/attributes`;
    // XXX: clean up error handling here at some point...
    const response = await get(endpoint);
    if (!response.ok) throw response.data;
    return response.data.map(attribute => [attribute.id, attribute.label]);
  }, [plugin]);

  // throw errors to the nearest error boundary
  if (error) throw error;
  const choices = loading ? LOADING_OPTION : value;
  return (
    <Select
      allowBlank
      choices={choices}
      id="id_attribute"
      disabled={loading || !plugin}
      {...fieldProps}
    />
  );
};

const IdentifierRoleField = () => {
  const [fieldProps] = useField('identifierRole');
  const choices = Object.entries(IDENTIFIER_ROLE_CHOICES);
  return (
    <Select
      choices={choices}
      id="id_identifierRole"
      translateChoices
      capfirstChoices
      {...fieldProps}
    />
  );
};

export default PrefillConfigurationForm;
