import {FieldArray, useFormikContext} from 'formik';
import isEqual from 'lodash/isEqual';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync, useToggle} from 'react-use';

import {APIContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import Select, {LOADING_OPTION} from 'components/admin/forms/Select';
import {post} from 'utils/fetch';

import {asJsonSchema} from './utils';

/**
 * Returns the Objects API Configuration editor modal for a specific variable. This only applies to V2 Options
 *
 * @typedef {{
 *   version: 1 | 2;
 *   objecttype: string;
 *   objecttypeVersion: number;
 *   variablesMapping: {variableKey: string, targetPath: string[]}[];
 * }} ObjectsAPIRegistrationBackendOptions
 *
 * @param {Object} p
 * @param {Object} p.variable - The current variable
 * @returns {JSX.Element} - The summary, represented as a the parts of the target path separated by '>'
 */
const ObjectsApiVariableConfigurationEditor = ({variable}) => {
  const {csrftoken} = useContext(APIContext);

  const [jsonSchemaVisible, toggleJsonSchemaVisible] = useToggle(false);
  const {values: backendOptions, getFieldProps, setFieldValue} = useFormikContext();

  /** @type {ObjectsAPIRegistrationBackendOptions} */
  const {objecttype, objecttypeVersion, variablesMapping, version} = backendOptions;
  if (version !== 2) throw new Error('Not supported, must be config version 2.');

  // get the index of our variable in the mapping, if it exists
  let index = variablesMapping.findIndex(
    mappedVariable => mappedVariable.variableKey === variable.key
  );
  let mappedVariable = variablesMapping[index];
  if (index === -1) {
    // if not found, grab the next available index to add it as a new record/entry
    index = variablesMapping.length;
    mappedVariable = {
      variableKey: variable.key,
      targetPath: undefined,
    };
    setFieldValue(`variablesMapping.${index}`, mappedVariable);
  }

  // the formik state is populated with the backend options, so our path needs to be
  // relative to that
  const namePrefix = `variablesMapping.${index}`;

  const {
    loading,
    value: targetPaths,
    error,
  } = useAsync(
    async () => {
      const response = await post(REGISTRATION_OBJECTS_TARGET_PATHS, csrftoken, {
        objecttypeUrl: objecttype,
        objecttypeVersion,
        variableJsonSchema: asJsonSchema(variable),
      });

      if (!response.ok) {
        throw new Error('Loading available target paths failed');
      }

      return response.data;
    },
    // Load only once:
    []
  );

  const getTargetPath = pathSegment => targetPaths.find(t => isEqual(t.targetPath, pathSegment));

  const choices =
    loading || error
      ? LOADING_OPTION
      : targetPaths.map(t => [JSON.stringify(t.targetPath), <TargetPathDisplay target={t} />]);

  return (
    <Fieldset>
      <FormRow>
        <Field
          name={`${namePrefix}.variableKey`}
          label={
            <FormattedMessage description="'Variable key' label" defaultMessage="Variable key" />
          }
        >
          <TextInput
            {...getFieldProps(`${namePrefix}.variableKey`)}
            value={mappedVariable.variableKey}
            readOnly
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.targetPath`}
          label={
            <FormattedMessage
              defaultMessage="JSON Schema target"
              description="'JSON Schema target' label"
            />
          }
        >
          <TargetPathSelect index={index} choices={choices} />
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

ObjectsApiVariableConfigurationEditor.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
};

const TargetPathSelect = ({name, index, choices}) => {
  const {getFieldProps, setFieldValue} = useFormikContext();
  const props = getFieldProps(name);

  return (
    <FieldArray
      name="variablesMapping"
      render={arrayHelpers => (
        <Select
          id="targetPath"
          name={name}
          allowBlank
          choices={choices}
          {...props}
          value={JSON.stringify(props.value)}
          onChange={event => {
            if (event.target.value === '') {
              arrayHelpers.remove(index);
            } else {
              setFieldValue(name, JSON.parse(event.target.value));
            }
          }}
        />
      )}
    />
  );
};

TargetPathSelect.propTypes = {
  name: PropTypes.string.isRequired,
  index: PropTypes.number.isRequired,
  choices: PropTypes.array.isRequired,
};

const TargetPathDisplay = ({target}) => {
  const path = target.targetPath.join(' > ');
  return (
    <FormattedMessage
      description="Representation of a JSON Schema target path"
      defaultMessage="{required, select, true {{path} (required)} other {{path}}}"
      values={{path, required: target.isRequired}}
    />
  );
};

TargetPathDisplay.propTypes = {
  target: PropTypes.shape({
    targetPath: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  isRequired: PropTypes.bool.isRequired,
};

export default ObjectsApiVariableConfigurationEditor;
