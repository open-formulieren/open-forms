import {FieldArray, useFormikContext} from 'formik';
import isEqual from 'lodash/isEqual';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync, useToggle} from 'react-use';

import {APIContext, FormContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import Select, {LOADING_OPTION} from 'components/admin/forms/Select';
import ErrorMessage from 'components/errors/ErrorMessage';
import {post} from 'utils/fetch';

import {asJsonSchema} from './utils';

/**
 * Returns the Objects API Configuration editor modal for a specific variable. This only applies to V2 Options
 *
 * @typedef {{
 *   version: 1 | 2;
 *   objectsApiGroup: number;
 *   objecttype: string;
 *   objecttypeVersion: number;
 *   variablesMapping: {variableKey: string, targetPath: string[]}[];
 *   geometryVariableKey: string;
 * }} ObjectsAPIRegistrationBackendOptions
 *
 * @param {Object} p
 * @param {Object} p.variable - The current variable
 * @returns {JSX.Element} - The configuration form for the Objects API
 */
const ObjectsApiVariableConfigurationEditor = ({variable}) => {
  const {csrftoken} = useContext(APIContext);
  const {components} = useContext(FormContext);
  const [jsonSchemaVisible, toggleJsonSchemaVisible] = useToggle(false);
  const {values: backendOptions, getFieldProps, setFieldValue} = useFormikContext();

  const hasAnyAddressNlValue = Object.values(variable.initialValue).some(value => value !== '');
  const [isSpecificTargetsChecked, setSpecificTargets] = useState(hasAnyAddressNlValue);

  /** @type {ObjectsAPIRegistrationBackendOptions} */
  const {
    objectsApiGroup,
    objecttype,
    objecttypeVersion,
    geometryVariableKey,
    variablesMapping,
    version,
  } = backendOptions;

  if (version !== 2) throw new Error('Not supported, must be config version 2.');

  const isGeometry = geometryVariableKey === variable.key;

  // get the index of our variable in the mapping, if it exists
  let index = variablesMapping.findIndex(
    mappedVariable => mappedVariable.variableKey === variable.key
  );

  if (index === -1) {
    // if not found, grab the next available index to add it as a new record/entry
    index = variablesMapping.length;
  }

  let mappedVariable = variablesMapping[index] || {
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
      const response = await post(REGISTRATION_OBJECTS_TARGET_PATHS, csrftoken, {
        objectsApiGroup,
        objecttype,
        objecttypeVersion,
        variableJsonSchema: asJsonSchema(variable, components),
      });
      if (!response.ok) {
        throw new Error('Error when loading target paths');
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

  if (error)
    return (
      <ErrorMessage>
        <FormattedMessage
          description="Objects API variable registration configuration API error"
          defaultMessage="Something went wrong when fetching the available target paths"
        />
      </ErrorMessage>
    );

  const isAddressNlComponent = components[variable?.key].type === 'addressNL';
  const deriveAddress = components[variable?.key]['deriveAddress'];

  const onSpecificTargetsChange = event => {
    setSpecificTargets(event.target.checked);
  };

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
      {!isAddressNlComponent && (
        <FormRow>
          <Field
            label={
              <FormattedMessage
                defaultMessage="Map to geometry field"
                description="'Map to geometry field' checkbox label"
              />
            }
            helpText={
              <FormattedMessage
                description="'Map to geometry field' checkbox help text"
                defaultMessage="Whether to map this variable to the {geometryPath} attribute"
                values={{geometryPath: <code>record.geometry</code>}}
              />
            }
            name="geometryVariableKey"
            disabled={!!mappedVariable.targetPath}
          >
            <Checkbox
              checked={isGeometry}
              onChange={event => {
                const newValue = event.target.checked ? variable.key : undefined;
                setFieldValue('geometryVariableKey', newValue);
              }}
            />
          </Field>
        </FormRow>
      )}
      <FormRow>
        <Field
          name={`${namePrefix}.targetPath`}
          label={
            <FormattedMessage
              defaultMessage="JSON Schema target"
              description="'JSON Schema target' label"
            />
          }
          disabled={isGeometry}
        >
          <TargetPathSelect
            name={`${namePrefix}.targetPath`}
            index={index}
            choices={choices}
            mappedVariable={mappedVariable}
            disabled={isGeometry}
          />
        </Field>
      </FormRow>
      {isAddressNlComponent && (
        <FormRow>
          <Field
            name={`${namePrefix}.nestedMapping`}
            label={
              <FormattedMessage
                defaultMessage="Define specific targets"
                description="Define specific targets for all the fields of AddressNL component"
              />
            }
          >
            <Checkbox checked={isSpecificTargetsChecked} onChange={onSpecificTargetsChange} />
          </Field>
        </FormRow>
      )}
      {isSpecificTargetsChecked && (
        <SpecificTargetsDisplay
          namePrefix={namePrefix}
          index={index}
          choices={choices}
          mappedVariable={mappedVariable}
          deriveAddress={deriveAddress}
        />
      )}
      <div style={{marginTop: '1em'}}>
        <a href="#" onClick={e => e.preventDefault() || toggleJsonSchemaVisible()}>
          <FormattedMessage
            description="Objects API variable configuration editor JSON Schema visibility toggle"
            defaultMessage="Toggle JSON Schema"
          />
        </a>
        {jsonSchemaVisible && (
          <pre style={{marginTop: '1em'}}>
            {loading || !mappedVariable.targetPath ? (
              <FormattedMessage description="Not applicable" defaultMessage="N/A" />
            ) : (
              JSON.stringify(getTargetPath(mappedVariable.targetPath).jsonSchema, null, 2)
            )}
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

const TargetPathSelect = ({id = 'targetPath', name, index, choices, mappedVariable, disabled}) => {
  // To avoid having an incomplete variable mapping added in the `variablesMapping` array,
  // It is added only when an actual target path is selected. This way, having the empty
  // option selected means the variable is unmapped (hence the `arrayHelpers.remove` call below).
  const {
    values: {variablesMapping},
    getFieldProps,
    setFieldValue,
  } = useFormikContext();
  const props = getFieldProps(name);
  const isNew = variablesMapping.length === index;

  return (
    <FieldArray
      name="variablesMapping"
      render={arrayHelpers => (
        <Select
          id={id}
          name={name}
          allowBlank
          choices={choices}
          {...props}
          disabled={disabled}
          value={JSON.stringify(props.value)}
          onChange={event => {
            if (event.target.value === '') {
              arrayHelpers.remove(index);
            } else {
              if (isNew) {
                arrayHelpers.push({...mappedVariable, targetPath: JSON.parse(event.target.value)});
              } else {
                setFieldValue(name, JSON.parse(event.target.value));
              }
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
  mappedVariable: PropTypes.object.isRequired,
};

const TargetPathDisplay = ({target}) => {
  const path = target.targetPath.length ? target.targetPath.join(' > ') : '/ (root)';
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
    isRequired: PropTypes.bool.isRequired,
  }).isRequired,
};

const SpecificTargetsDisplay = ({namePrefix, index, choices, mappedVariable, deriveAddress}) => {
  console.log(mappedVariable);
  return (
    <Fieldset>
      <FormRow>
        <Field
          name={`${namePrefix}.postcodeTargetPath`}
          label={
            <FormattedMessage
              defaultMessage="Postcode Schema target"
              description="'Postcode Schema target' label"
            />
          }
        >
          <TargetPathSelect
            id="postcodeTargetPath"
            name={`${namePrefix}.postcodeTargetPath`}
            index={index}
            choices={choices}
            mappedVariable={mappedVariable}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.houseNumberTargetPath`}
          label={
            <FormattedMessage
              defaultMessage="House number Schema target"
              description="'House number Schema target' label"
            />
          }
        >
          <TargetPathSelect
            id="houseNumberTargetPath"
            name={`${namePrefix}.houseNumberTargetPath`}
            index={index}
            choices={choices}
            mappedVariable={mappedVariable}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.houseLetterTargetPath`}
          label={
            <FormattedMessage
              defaultMessage="House letter Schema target"
              description="'House letter Schema target' label"
            />
          }
        >
          <TargetPathSelect
            id="houseLetterTargetPath"
            name={`${namePrefix}.houseLetterTargetPath`}
            index={index}
            choices={choices}
            mappedVariable={mappedVariable}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.houseNumberAdditionTargetPath`}
          label={
            <FormattedMessage
              defaultMessage="House number addition Schema target"
              description="'House number addition Schema target' label"
            />
          }
        >
          <TargetPathSelect
            id="houseNumberAdditionTargetPath"
            name={`${namePrefix}.houseNumberAdditionTargetPath`}
            index={index}
            choices={choices}
            mappedVariable={mappedVariable}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.cityTargetPath`}
          label={
            <FormattedMessage
              defaultMessage="City Schema target"
              description="'City Schema target' label"
            />
          }
          disabled={!deriveAddress}
        >
          <TargetPathSelect
            id="cityTargetPath"
            name={`${namePrefix}.cityTargetPath`}
            index={index}
            choices={choices}
            mappedVariable={mappedVariable}
            disabled={!deriveAddress}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.streetNameTargetPath`}
          label={
            <FormattedMessage
              defaultMessage="Street name Schema target"
              description="'Street name Schema target' label"
            />
          }
          disabled={!deriveAddress}
        >
          <TargetPathSelect
            id="streetNameTargetPath"
            name={`${namePrefix}.streetNameTargetPath`}
            index={index}
            choices={choices}
            mappedVariable={mappedVariable}
            disabled={!deriveAddress}
          />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

export default ObjectsApiVariableConfigurationEditor;
