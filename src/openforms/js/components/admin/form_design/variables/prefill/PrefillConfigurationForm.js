import {Formik, useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
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
import VariableMapping from 'components/admin/forms/VariableMapping';
import {
  ObjectTypeSelect,
  ObjectTypeVersionSelect,
  ObjectsAPIGroup,
} from 'components/admin/forms/objects_api';
import {FAIcon} from 'components/admin/icons';
import ErrorBoundary from 'components/errors/ErrorBoundary';
import {get} from 'utils/fetch';

import {IDENTIFIER_ROLE_CHOICES} from '../constants';

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
            {<PluginFormComponent values={values} errors={errors} />}

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

const AttributeField = ({prefillAttributes}) => {
  const [fieldProps] = useField('attribute');
  const {
    values: {plugin},
  } = useFormikContext();

  return (
    <Select
      allowBlank
      choices={prefillAttributes}
      id="id_attribute"
      disabled={!plugin}
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

const PrefillFields = ({values, errors}) => {
  // Load the possible prefill attributes
  // XXX: this would benefit from client-side caching
  const plugin = values.plugin;
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
  const prefillAttributes = loading ? LOADING_OPTION : value;

  return (
    <Fieldset>
      <FormRow>
        <Field
          name="plugin"
          label={
            <FormattedMessage description="Variable prefill plugin label" defaultMessage="Plugin" />
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
          <AttributeField prefillAttributes={prefillAttributes} />
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
  );
};

/**
 * Callback to invoke when the API group changes - used to reset the dependent fields.
 */
const onApiGroupChange = prevValues => ({
  ...prevValues,
  options: {
    ...prevValues.options,
    objecttype: '',
    objecttypeVersion: undefined,
    variablesMapping: [],
  },
});

const ObjectsAPIPrefillFields = ({values, errors}) => {
  const intl = useIntl();
  const plugin = values.plugin;

  const {
    plugins: {availablePrefillPlugins},
  } = useContext(FormContext);
  const {setFieldValue} = useFormikContext();
  const objectsPlugin = availablePrefillPlugins.find(elem => elem.id === 'objects_api');

  const apiGroups = objectsPlugin.configurationContext.apiGroups;

  const {objecttype, objecttypeVersion, objectsApiGroup} = values.options;

  // Load the possible prefill properties
  // XXX: this would benefit from client-side caching
  const {
    loading,
    value = [],
    error,
  } = useAsync(async () => {
    if (!plugin || !objecttype || !objecttypeVersion || !objectsApiGroup) return [];

    const endpoint = `/api/v2/prefill/plugins/objects-api/objecttypes/${objecttype}/versions/${objecttypeVersion}/properties`;
    // XXX: clean up error handling here at some point...
    const response = await get(endpoint, {objects_api_group: objectsApiGroup});
    if (!response.ok) throw response.data;

    return response.data.map(property => [property.targetPath, property.targetPath.join(' > ')]);
  }, [plugin, objecttype, objecttypeVersion, objectsApiGroup]);

  // throw errors to the nearest error boundary
  if (error) throw error;
  const prefillProperties = loading ? LOADING_OPTION : value;

  return (
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

        <ObjectsAPIGroup
          name="options.objectsApiGroup"
          prefix="options"
          apiGroupChoices={apiGroups}
          onChangeCheck={() => {
            if (values.options.variablesMapping.length === 0) return true;
            const confirmSwitch = window.confirm(
              intl.formatMessage({
                description:
                  'Objects API registration options: warning message when changing the api group',
                defaultMessage: `Changing the api group will remove the existing variables mapping.
                Are you sure you want to continue?`,
              })
            );
            if (!confirmSwitch) return false;
            setFieldValue('options.variablesMapping', []);
            return true;
          }}
          onApiGroupChange={onApiGroupChange}
        />

        <ErrorBoundary
          errorMessage={
            <FormattedMessage
              description="Objects API registrations options: object type select error"
              defaultMessage="Something went wrong while retrieving the available object types."
            />
          }
        >
          <ObjectTypeSelect
            name="options.objecttype"
            apiGroupFieldName="options.objectsApiGroup"
            versionFieldName="options.objecttypeVersion"
            onChangeCheck={() => {
              if (values.options.variablesMapping.length === 0) return true;
              const confirmSwitch = window.confirm(
                intl.formatMessage({
                  description:
                    'Objects API registration options: warning message when changing the object type',
                  defaultMessage: `Changing the objecttype will remove the existing variables mapping.
                  Are you sure you want to continue?`,
                })
              );
              if (!confirmSwitch) return false;
              setFieldValue('options.variablesMapping', []);
              return true;
            }}
          />
        </ErrorBoundary>

        <ErrorBoundary
          errorMessage={
            <FormattedMessage
              description="Objects API registrations options: object type version select error"
              defaultMessage="Something went wrong while retrieving the available object type versions."
            />
          }
        >
          <ObjectTypeVersionSelect
            name="options.objecttypeVersion"
            apiGroupFieldName="options.objectsApiGroup"
            objectTypeFieldName="options.objecttype"
          />
        </ErrorBoundary>
      </Fieldset>

      <Fieldset
        title={
          <FormattedMessage
            description="Objects API prefill mappings fieldset title"
            defaultMessage="Mappings"
          />
        }
      >
        <FormRow>
          <VariableMapping
            name="options.variablesMapping"
            loading={loading}
            directionIcon={<FAIcon icon="arrow-left-long" aria-hidden="true" />}
            propertyName="prefillProperty"
            propertyChoices={prefillProperties}
            propertyHeading={
              <FormattedMessage
                description="Prefill / Objects API: column header for object type property selection"
                defaultMessage="Source path"
              />
            }
            propertySelectLabel={intl.formatMessage({
              description:
                'Prefill / Objects API: accessible label for object type property selection',
              defaultMessage: 'Select a property from the object type',
            })}
          />
        </FormRow>
      </Fieldset>
    </>
  );
};

const PLUGIN_COMPONENT_MAPPING = {
  objects_api: ObjectsAPIPrefillFields,
  default: PrefillFields,
};

export default PrefillConfigurationForm;
