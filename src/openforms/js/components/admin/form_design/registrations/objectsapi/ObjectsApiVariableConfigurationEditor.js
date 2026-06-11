import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext, useEffect} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

import AddressNLEditor from './edit_options/AddressNLEditor';
import MapEditor from './edit_options/MapEditor';
import SelectboxesEditor from './edit_options/SelectboxesEditor';
import {GenericEditor} from './edit_options/generic';

// This can be updated with component-specific variable configuration options which do not
// adhere to the generic behaviour (GenericEditor)
const VARIABLE_CONFIGURATION_OPTIONS = {
  addressNL: AddressNLEditor,
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
  const {values: backendOptions, getFieldProps, setFieldValue} = useFormikContext();
  const {components} = useContext(FormContext);

  /** @type {ObjectsAPIRegistrationBackendOptions} */
  const {objectsApiGroup, objecttype, objecttypeVersion, variablesMapping, version} =
    backendOptions;

  if (version !== 2) throw new Error('Not supported, must be config version 2.');

  // get the index of our variable in the mapping, if it exists
  const index = variablesMapping.findIndex(
    mappedVariable => mappedVariable.variableKey === variable.key
  );

  // ensure that the mapping entry is present for the variable, if not -> insert it.
  useEffect(() => {
    if (index === -1) {
      const newVariablesMapping = [
        ...variablesMapping,
        {
          variableKey: variable.key,
          targetPath: undefined,
          // options are added dynamically by the component type specific editor
        },
      ];
      setFieldValue('variablesMapping', newVariablesMapping);
    }
  }, []);

  // ideally we'd manage validation errors to block modal form submission, but we don't
  // have a generic way to test this and can only rely on backend validation :(.
  // To be able to do this, we need to seriously rework our code structure here.

  // Render nothing until the effect above has completed and actually adds the mapping
  // to the formik state.
  if (index === -1) return null;

  const mappedVariable = variablesMapping[index];
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
            required
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
