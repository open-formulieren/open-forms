import {useFormikContext} from 'formik';
import isEqual from 'lodash/isEqual';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync, useToggle} from 'react-use';

import {APIContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';
import ErrorMessage from 'components/errors/ErrorMessage';

import {MappedVariableTargetPathSelect} from './GenericObjectsApiVariableConfigurationEditor';
import {fetchTargetPaths} from './utils';
import {asJsonSchema} from './utils';

export const MapEditor = ({
  variable,
  components,
  namePrefix,
  index,
  mappedVariable,
  objecttype,
  objectsApiGroup,
  objecttypeVersion,
  backendOptions,
}) => {
  const {csrftoken} = useContext(APIContext);
  const [jsonSchemaVisible, toggleJsonSchemaVisible] = useToggle(false);
  const {setFieldValue} = useFormikContext();
  const {geometryVariableKey} = backendOptions;

  const isGeometry = geometryVariableKey && geometryVariableKey === variable.key;

  // Load all the possible target paths in parallel
  const {
    loading,
    value: targetPaths,
    error,
  } = useAsync(async () => {
    const results = fetchTargetPaths(
      csrftoken,
      objectsApiGroup,
      objecttype,
      objecttypeVersion,
      asJsonSchema(variable, components)
    );
    return results;
  }, []);

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
