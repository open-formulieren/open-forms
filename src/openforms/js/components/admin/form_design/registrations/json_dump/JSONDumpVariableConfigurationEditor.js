import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {VARIABLE_SOURCES} from 'components/admin/form_design/variables/constants';
import {getVariableSource} from 'components/admin/form_design/variables/utils';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

import {CUSTOM_COMPONENTS_SCHEMA} from '../utils';

const JSONDumpVariableConfigurationEditor = ({variable}) => {
  const {
    values: {
      variables = [],
      additionalMetadataVariables = [],
      fixedMetadataVariables = [],
      transformToList = {},
    },
    setFieldValue,
  } = useFormikContext();
  const {components} = useContext(FormContext);
  const isIncluded = variables.includes(variable.key);
  const isRequiredInMetadata = fixedMetadataVariables.includes(variable.key);
  const isInAdditionalMetadata = additionalMetadataVariables.includes(variable.key);
  const componentType = components[variable?.key]?.type;

  return (
    <>
      <FormRow>
        <Field name="includeVariable">
          <Checkbox
            name="includeVariableCheckbox"
            label={
              <FormattedMessage
                description="'Include variable' checkbox label"
                defaultMessage="Include variable"
              />
            }
            helpText={
              <FormattedMessage
                description="'Include variable' checkbox help text"
                defaultMessage="Whether to include this variable in the data to be sent."
              />
            }
            checked={isIncluded}
            onChange={event => {
              const shouldBeIncluded = event.target.checked;
              const newVariables = shouldBeIncluded
                ? [...variables, variable.key] // add the variable to the array
                : variables.filter(key => key !== variable.key); // remove the variable from the array
              setFieldValue('variables', newVariables);
            }}
          />
        </Field>
      </FormRow>

      <FormRow>
        <Field name="includeVariableInMetadata">
          <Checkbox
            name="includeVariableInMetadataCheckbox"
            label={
              <FormattedMessage
                description="'Include variable in metadata' checkbox label"
                defaultMessage="Include variable in metadata"
              />
            }
            helpText={
              <FormattedMessage
                description="'Include variable in metadata' checkbox help text"
                defaultMessage="Whether to include this variable in the metadata to be sent."
              />
            }
            checked={isInAdditionalMetadata || isRequiredInMetadata}
            onChange={event => {
              const shouldBeIncluded = event.target.checked;
              const newVariables = shouldBeIncluded
                ? [...additionalMetadataVariables, variable.key] // add the variable to the array
                : additionalMetadataVariables.filter(key => key !== variable.key); // remove the variable from the array
              setFieldValue('additionalMetadataVariables', newVariables);
            }}
            disabled={
              isRequiredInMetadata || getVariableSource(variable) !== VARIABLE_SOURCES.static
            } // disable if it is required or the variable is not a static variable
          />
        </Field>
      </FormRow>

      {componentType in CUSTOM_COMPONENTS_SCHEMA && (
        <FormRow>
          <Field name={`transformToList.${variable.key}`}>
            <Checkbox
              name="transformToListCheckbox"
              label={
                <FormattedMessage
                  defaultMessage="Transform to list"
                  description="'Transform to list' checkbox label"
                />
              }
              helpText={
                <FormattedMessage
                  description="'Transform to list' checkbox help text"
                  defaultMessage="Whether to transform the data of the component to a list or not (depends on the component type)"
                />
              }
              checked={transformToList?.[variable.key] || false}
              onChange={e => setFieldValue(`transformToList.${variable.key}`, e.target.checked)}
            />
          </Field>
        </FormRow>
      )}
    </>
  );
};

JSONDumpVariableConfigurationEditor.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
};

export default JSONDumpVariableConfigurationEditor;
