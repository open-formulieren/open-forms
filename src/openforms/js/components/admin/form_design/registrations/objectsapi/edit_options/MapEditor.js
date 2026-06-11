import {useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';
import {TargetPathSelect} from 'components/admin/forms/objects_api';
import ErrorMessage from 'components/errors/ErrorMessage';

import {ShowJSONSchemaToggle, TargetPath} from './generic';
import {useFetchTargetPaths, useVariableJsonSchema} from './hooks';

const MapEditor = ({
  variable,
  components,
  namePrefix,
  mappedVariable,
  objecttype,
  objectsApiGroup,
  objecttypeVersion,
  backendOptions,
}) => {
  const {setFieldValue} = useFormikContext();
  const {geometryVariableKey} = backendOptions;

  const isGeometry = geometryVariableKey && geometryVariableKey === variable.key;

  const variableSchema = useVariableJsonSchema(variable, components);
  const {loading, targetPaths, error} = useFetchTargetPaths({
    objectsApiGroup,
    objecttype,
    objecttypeVersion,
    variableJsonSchema: variableSchema,
  });

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
      <TargetPath
        namePrefix={namePrefix}
        loading={loading}
        targetPaths={targetPaths}
        isDisabled={isGeometry}
      />
      <ShowJSONSchemaToggle availablePaths={targetPaths} targetPath={mappedVariable.targetPath} />
    </>
  );
};

export default MapEditor;
