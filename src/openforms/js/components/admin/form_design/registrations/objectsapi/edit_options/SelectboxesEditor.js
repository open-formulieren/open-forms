import {useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';
import ErrorMessage from 'components/errors/ErrorMessage';

import {ShowJSONSchemaToggle, TargetPath} from './generic';
import {useFetchTargetPaths, useVariableJsonSchema} from './hooks';

const SelectboxesEditor = ({
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
  const {transformToList = []} = backendOptions;

  // don't use the destructured object with default, as that triggers hook re-evaluation!
  const variableSchema = useVariableJsonSchema(
    variable,
    components,
    backendOptions.transformToList
  );
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
            checked={transformToList.includes(variable.key) || false}
            onChange={event => {
              const shouldBeTransformed = event.target.checked;
              const newTransformToList = shouldBeTransformed
                ? [...transformToList, variable.key]
                : transformToList.filter(key => key !== variable.key);
              setFieldValue('transformToList', newTransformToList);
              setFieldValue(`${namePrefix}.targetPath`, undefined);
            }}
          />
        </Field>
      </FormRow>
      <TargetPath namePrefix={namePrefix} loading={loading} targetPaths={targetPaths} />
      <ShowJSONSchemaToggle availablePaths={targetPaths} targetPath={mappedVariable.targetPath} />
    </>
  );
};

export default SelectboxesEditor;
