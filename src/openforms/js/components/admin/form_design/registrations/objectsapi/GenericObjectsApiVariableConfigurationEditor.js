import {FieldArray, useFormikContext} from 'formik';
import isEqual from 'lodash/isEqual';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync, useToggle} from 'react-use';

import {APIContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';
import {TargetPathSelect} from 'components/admin/forms/objects_api';
import ErrorMessage from 'components/errors/ErrorMessage';
import {post} from 'utils/fetch';

import {asJsonSchema} from './utils';

/**
 * Hack-ish way to manage the variablesMapping state for one particular entry.
 *
 * We ensure that an item is added to `variablesMapping` by using the `FieldArray`
 * helper component if it doesn't exist yet, otherwise we update it.
 */
export const MappedVariableTargetPathSelect = ({
  name,
  index,
  mappedVariable,
  isLoading = false,
  targetPaths = [],
  isDisabled = false,
}) => {
  const {
    values: {variablesMapping = []},
    setFieldValue,
  } = useFormikContext();
  const isNew = variablesMapping.length === index;
  return (
    <FieldArray
      name="variablesMapping"
      render={arrayHelpers => (
        <TargetPathSelect
          name={name}
          isLoading={isLoading}
          targetPaths={targetPaths}
          isDisabled={isDisabled}
          onChange={newValue => {
            // Clearing the select means we need to remove the record from the mapping,
            // otherwise it's not a valid item for the backend.
            if (newValue === null) {
              arrayHelpers.remove(index);
              return;
            }

            // otherwise, either add a new item, or update the existing
            if (isNew) {
              const newMapping = {...mappedVariable, targetPath: newValue.targetPath};
              arrayHelpers.push(newMapping);
            } else {
              setFieldValue(name, newValue.targetPath);
            }
          }}
        />
      )}
    />
  );
};

MappedVariableTargetPathSelect.propTypes = {
  name: PropTypes.string.isRequired,
  index: PropTypes.number.isRequired,
  mappedVariable: PropTypes.shape({
    variableKey: PropTypes.string.isRequired,
    targetPath: PropTypes.arrayOf(PropTypes.string),
    options: PropTypes.object,
  }).isRequired,
  isLoading: PropTypes.bool,
  isDisabled: PropTypes.bool,
};

export const GenericEditor = ({
  variable,
  components,
  namePrefix,
  isGeometry,
  index,
  mappedVariable,
  objecttype,
  objectsApiGroup,
  objecttypeVersion,
}) => {
  const {csrftoken} = useContext(APIContext);
  const [jsonSchemaVisible, toggleJsonSchemaVisible] = useToggle(false);
  const {setFieldValue} = useFormikContext();

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

  if (error)
    return (
      <ErrorMessage>
        <FormattedMessage
          description="Objects API variable registration configuration API error"
          defaultMessage="Something went wrong when fetching the available target paths"
        />
      </ErrorMessage>
    );
  return (
    <>
      <FormRow>
        <Field name="geometryVariableKey" disabled={!!mappedVariable.targetPath}>
          <Checkbox
            name="geometryCheckbox"
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
            checked={isGeometry}
            onChange={event => {
              const newValue = event.target.checked ? variable.key : undefined;
              setFieldValue('geometryVariableKey', newValue);
            }}
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
          disabled={isGeometry}
        >
          <MappedVariableTargetPathSelect
            name={`${namePrefix}.targetPath`}
            index={index}
            mappedVariable={mappedVariable}
            isDisabled={isGeometry}
            isLoading={loading}
            targetPaths={targetPaths}
          />
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
          <pre style={{marginTop: '1em'}}>
            {loading || !mappedVariable.targetPath ? (
              <FormattedMessage description="Not applicable" defaultMessage="N/A" />
            ) : (
              JSON.stringify(getTargetPath(mappedVariable.targetPath).jsonSchema, null, 2)
            )}
          </pre>
        )}
      </div>
    </>
  );
};
