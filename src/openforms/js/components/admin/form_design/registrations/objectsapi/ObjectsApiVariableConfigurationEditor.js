import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

import {AddressNlEditor} from './AddressNlObjectsApiVariableConfigurationEditor';
import {GenericEditor} from './GenericObjectsApiVariableConfigurationEditor';
import {MapEditor} from './MapObjectsApiVariableConfigurationEditor';
import {SelectboxesEditor} from './SelectboxesObjectsApiVariableConfigurationEditor';

// This can be updated with component-specific variable configuration options which do not
// adhere to the generic behaviour (GenericEditor)
const VARIABLE_CONFIGURATION_OPTIONS = {
  addressNL: AddressNlEditor,
  map: MapEditor,
  selectboxes: SelectboxesEditor,
};

/**
 * Returns the Objects API Configuration editor modal for a specific variable and a specific
 * component type. This only applies to V2 Options
 *
 * @typedef {{
 *   version: 1 | 2;
 *   objectsApiGroup: string;
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
  const {values: backendOptions, getFieldProps} = useFormikContext();
  const {components} = useContext(FormContext);

  /** @type {ObjectsAPIRegistrationBackendOptions} */
  const {objectsApiGroup, objecttype, objecttypeVersion, variablesMapping, version} =
    backendOptions;

  if (version !== 2) throw new Error('Not supported, must be config version 2.');

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
  // check if there is a specific ConfigurationEditor according to the variable type,
  // if not, fallback to the default/generic one
  const componentType = components[variable?.key]?.type;
  const VariableConfigurationEditor =
    VARIABLE_CONFIGURATION_OPTIONS?.[componentType] ?? GenericEditor;

  return (
    <>
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
        <VariableConfigurationEditor
          variable={variable}
          components={components}
          namePrefix={namePrefix}
          index={index}
          mappedVariable={mappedVariable}
          objecttype={objecttype}
          objectsApiGroup={objectsApiGroup}
          objecttypeVersion={objecttypeVersion}
          backendOptions={backendOptions}
        />
      </Fieldset>
    </>
  );
};

ObjectsApiVariableConfigurationEditor.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
};

export {ObjectsApiVariableConfigurationEditor};
