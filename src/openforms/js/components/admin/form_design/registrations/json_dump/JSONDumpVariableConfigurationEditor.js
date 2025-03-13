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

const JSONDumpVariableConfigurationEditor = ({variable}) => {
  const {
    values: {
      variables = [],
      additionalMetadataVariables = [],
      fixedMetadataVariables = [],
      transformToList = [],
    },
    setFieldValue,
  } = useFormikContext();
  const {components} = useContext(FormContext);
  const isIncluded = variables.includes(variable.key);
  const isRequiredInMetadata = fixedMetadataVariables.includes(variable.key);
  const isInAdditionalMetadata = additionalMetadataVariables.includes(variable.key);
  const componentType = components[variable.key]?.type;
  const transformationNeeded = transformToList.includes(variable.key);

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

      {componentType === 'selectboxes' && (
        <FormRow>
          <Field name="transformToList">
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
                  defaultMessage="If enabled, the selected values are sent as an array of values instead of an object with a boolean value for each option."
                />
              }
              checked={transformationNeeded || false}
              onChange={event => {
                const shouldBeTransformed = event.target.checked;
                const newTransformToList = shouldBeTransformed
                  ? [...transformToList, variable.key]
                  : transformToList.filter(key => key !== variable.key);
                setFieldValue('transformToList', newTransformToList);
              }}
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
