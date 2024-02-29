import {useFormikContext} from 'formik';
import isEqual from 'lodash/isEqual';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync, useToggle} from 'react-use';

import {FormContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import Select, {LOADING_OPTION} from 'components/admin/forms/Select';
import {get} from 'utils/fetch';

/**
 * Returns the Objects API Configuration editor modal for a specific variable. This only applies to V2 Options
 *
 * @typedef {{
 *   backend: string;
 *   key: string;
 *   name: string;
 *   options: {
 *     variablesMapping: {variableKey: string, targetPath: string[]}[]
 *   }
 * }} ObjectsAPIRegistrationBackend
 *
 * @param {Object} p
 * @param {Object} p.variable - The current variable
 * @param {ObjectsAPIRegistrationBackend} p.backend - The Objects API registration backend (options guaranteed to be v2)
 * @returns {JSX.Element} - The summary, represented as a the parts of the target path separated by '>'
 */
const ObjectsApiVariableConfigurationEditor = ({variable, backend}) => {
  const {
    form: {uuid},
  } = useContext(FormContext);

  const [jsonSchemaVisible, toggleJsonSchemaVisible] = useToggle(false);
  const {values: backendOptions, getFieldProps} = useFormikContext();

  const {objecttype, objecttypeVersion, variablesMapping, version} = backendOptions;
  if (version !== 2) throw new Error('Not supported, must be config version 2.');

  console.log(
    `Configuring variable mapping for objecttype ${objecttype}, version ${objecttypeVersion}`
  );

  // get the index of our variable in the mapping, if it exists
  let index = variablesMapping.findIndex(
    mappedVariable => mappedVariable.variableKey === variable.key
  );
  // if not found, grab the next available index to add it as a new record/entry
  if (index === -1) {
    index = variablesMapping.length;
  }

  const mappedVariable = variablesMapping[index] || {
    variableKey: variable.key,
    targetPath: undefined,
  };

  // the formik state is populated with the backend options, so our path needs to be
  // relative to that
  const namePrefix = `variablesMapping.${index}`;

  const {
    loading,
    value: targetPaths,
    error,
  } = useAsync(
    async () => {
      const response = await get(REGISTRATION_OBJECTS_TARGET_PATHS, {
        backendKey: backend.key,
        formUuid: uuid,
        variableKey: variable.key,
      });

      if (!response.ok) {
        throw new Error('Loading available target paths failed');
      }

      return response.data;
    },
    // Load only once:
    []
  );

  const getTargetPath = pathSegment =>
    targetPaths.find(t => isEqual(t.targetPath, JSON.parse(pathSegment)));

  const choices =
    loading || error
      ? LOADING_OPTION
      : targetPaths.map(t => [
          JSON.stringify(t.targetPath),
          `${t.targetPath.join(' > ')}${t.required ? ' (required)' : ''}`,
        ]);

  return (
    <Fieldset>
      <FormRow>
        <Field
          name={`${namePrefix}.key`}
          label={
            <FormattedMessage description="'Variable key' label" defaultMessage="Variable key" />
          }
        >
          <TextInput
            {...getFieldProps(`${namePrefix}.key`)}
            value={mappedVariable.variableKey}
            readOnly
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.targetPath`}
          htmlFor="targetPath"
          label={
            <FormattedMessage
              defaultMessage="JSON Schema target"
              description="'JSON Schema target' label"
            />
          }
        >
          <TargetPathSelect name={`${namePrefix}.targetPath`} choices={choices} />
        </Field>
      </FormRow>
      <div style={{marginTop: '1em'}}>
        <a href="#" onClick={e => e.preventDefault() || toggleJsonSchemaVisible()}>
          <FormattedMessage
            description="Objects API variable configuration editor JSON Schema visibility toggle"
            defaultMessage="Toggle JSON Schema"
          />
        </a>
        {jsonSchemaVisible && (
          <pre>
            {loading || !mappedVariable.targetPath
              ? 'N/A'
              : JSON.stringify(getTargetPath(mappedVariable.targetPath).jsonSchema, null, 2)}
          </pre>
        )}
      </div>
    </Fieldset>
  );
};

const TargetPathSelect = ({name, choices}) => {
  const {getFieldProps, setFieldValue} = useFormikContext();
  const props = getFieldProps(name);

  return (
    <Select
      id="targetPath"
      name={name}
      allowBlank
      choices={choices}
      {...props}
      value={JSON.stringify(props.value)}
      onChange={event => {
        setFieldValue(name, JSON.parse(event.target.value));
      }}
    />
  );
};

export default ObjectsApiVariableConfigurationEditor;
