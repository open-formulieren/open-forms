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
import Select, {LOADING_OPTION} from 'components/admin/forms/Select';
import ErrorMessage from 'components/errors/ErrorMessage';
import {post} from 'utils/fetch';

import {TargetPathDisplay} from './ObjectsApiVariableConfigurationEditor';
import {asJsonSchema} from './utils';

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
          <TargetPathSelect
            name={`${namePrefix}.targetPath`}
            index={index}
            choices={choices}
            mappedVariable={mappedVariable}
            disabled={isGeometry}
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

const TargetPathSelect = ({name, index, choices, mappedVariable, disabled}) => {
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
          id="targetPath"
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
