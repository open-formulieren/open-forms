import {FormattedMessage} from 'react-intl';

import ErrorMessage from 'components/errors/ErrorMessage';

import {ShowJSONSchemaToggle, TargetPath} from '.';
import {useFetchTargetPaths, useVariableJsonSchema} from '../hooks';

const GenericEditor = ({
  variable,
  components,
  namePrefix,
  mappedVariable,
  objecttype,
  objectsApiGroup,
  objecttypeVersion,
}) => {
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
      <TargetPath namePrefix={namePrefix} loading={loading} targetPaths={targetPaths} />
      <ShowJSONSchemaToggle availablePaths={targetPaths} targetPath={mappedVariable.targetPath} />
    </>
  );
};

export default GenericEditor;
