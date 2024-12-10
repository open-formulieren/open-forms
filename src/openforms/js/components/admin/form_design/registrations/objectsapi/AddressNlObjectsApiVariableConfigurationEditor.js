import {useFormikContext} from 'formik';
import isEqual from 'lodash/isEqual';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync, useToggle} from 'react-use';

import {APIContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';
import {TargetPathSelect} from 'components/admin/forms/objects_api';
import ErrorMessage from 'components/errors/ErrorMessage';
import {post} from 'utils/fetch';

import {MappedVariableTargetPathSelect} from './GenericObjectsApiVariableConfigurationEditor';

const ADDRESSNL_NESTED_PROPERTIES = {
  postcode: {type: 'string'},
  houseLetter: {type: 'string'},
  houseNumber: {type: 'number'},
  houseNumberAddition: {type: 'string'},
  city: {type: 'string'},
  streetName: {type: 'string'},
};

const fetchTargetPaths = async (
  csrftoken,
  objectsApiGroup,
  objecttype,
  objecttypeVersion,
  schemaType
) => {
  const response = await post(REGISTRATION_OBJECTS_TARGET_PATHS, csrftoken, {
    objectsApiGroup,
    objecttype,
    objecttypeVersion,
    variableJsonSchema: schemaType,
  });

  if (!response.ok) {
    throw new Error(`Error when loading target paths for type: ${schemaType}`);
  }

  return response.data;
};

export const AddressNlEditor = ({
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
  const {setValues} = useFormikContext();

  const hasSpecificOptions = Object.values(mappedVariable?.options ?? {}).some(
    targetPath => targetPath && targetPath.length
  );
  const [specificTargetPaths, toggleSpecificTargetPaths] = useToggle(hasSpecificOptions);
  const [jsonSchemaVisible, toggleJsonSchemaVisible] = useToggle(false);

  const deriveAddress = components[variable?.key]['deriveAddress'];

  // Load all the possible target paths (obect,string and number types) in parallel and only once
  const {
    loading,
    value: targetPaths,
    error,
  } = useAsync(async () => {
    const schemaTypes = [
      {type: 'object', properties: ADDRESSNL_NESTED_PROPERTIES},
      {type: 'string'},
      {type: 'number'},
    ];

    const promises = schemaTypes.map(type =>
      fetchTargetPaths(csrftoken, objectsApiGroup, objecttype, objecttypeVersion, type)
    );

    const results = await Promise.all(promises);
    return results;
  }, []);

  const [objectTypeTargetPaths = [], stringTypeTargetPaths = [], numberTypeTargetPaths = []] =
    targetPaths || [];

  const getTargetPath = pathSegment =>
    objectTypeTargetPaths.find(t => isEqual(t.targetPath, pathSegment));

  if (error)
    return (
      <ErrorMessage>
        <FormattedMessage
          description="Objects API variable registration configuration API error"
          defaultMessage="Something went wrong when fetching the available target paths"
        />
      </ErrorMessage>
    );

  const onSpecificTargetPathsChange = event => {
    const makeSpecific = event.target.checked;
    toggleSpecificTargetPaths(makeSpecific);

    setValues(prevValues => {
      const newVariablesMapping = [...prevValues.variablesMapping];
      const newMappedVariable = {
        ...(newVariablesMapping[index] ?? mappedVariable),
        // clear targetPath if we're switching to specific subfields
        targetPath: makeSpecific ? undefined : mappedVariable.targetPath,
        // prepare the options structure if we're switching to specific subfields,
        // otherwise remove it entirely
        options: makeSpecific
          ? {
              postcode: undefined,
              houseLetter: undefined,
              houseNumber: undefined,
              houseNumberAddition: undefined,
              city: undefined,
              streetName: undefined,
            }
          : undefined,
      };
      newVariablesMapping[index] = newMappedVariable;
      return {...prevValues, variablesMapping: newVariablesMapping};
    });
  };

  return (
    <>
      <FormRow>
        <Checkbox
          name="specificTargetPathsCheckbox"
          label={
            <FormattedMessage
              defaultMessage="Map specific subfields"
              description="'Map specific subfields' checkbox label"
            />
          }
          helpText={
            <FormattedMessage
              description="'Map specific subfields' checkbox help text"
              defaultMessage="Whether to map the specific subfield of addressNl component"
            />
          }
          checked={specificTargetPaths}
          onChange={onSpecificTargetPathsChange}
          disabled={!!mappedVariable.targetPath}
        />
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.targetPath`}
          label={
            <FormattedMessage
              defaultMessage="JSON Schema object target"
              description="'JSON Schema object target' label"
            />
          }
          disabled={specificTargetPaths}
        >
          <MappedVariableTargetPathSelect
            name={`${namePrefix}.targetPath`}
            index={index}
            mappedVariable={mappedVariable}
            isDisabled={isGeometry || specificTargetPaths}
            isLoading={loading}
            targetPaths={objectTypeTargetPaths}
          />
        </Field>
      </FormRow>
      {specificTargetPaths && (
        <Fieldset>
          <FormRow>
            <Field
              name={`${namePrefix}.options.postcode`}
              label={
                <FormattedMessage
                  defaultMessage="Postcode Schema target"
                  description="Objects registration variable mapping, addressNL component: 'options.postcode schema target' label"
                />
              }
              required
              noManageChildProps
            >
              <TargetPathSelect
                name={`${namePrefix}.options.postcode`}
                isLoading={loading}
                targetPaths={stringTypeTargetPaths}
              />
            </Field>
          </FormRow>
          <FormRow>
            <Field
              name={`${namePrefix}.options.houseNumber`}
              label={
                <FormattedMessage
                  defaultMessage="House number Schema target"
                  description="Objects registration variable mapping, addressNL component: 'options.houseNumber schema target' label"
                />
              }
              required
              noManageChildProps
            >
              <TargetPathSelect
                name={`${namePrefix}.options.houseNumber`}
                isLoading={loading}
                targetPaths={numberTypeTargetPaths}
              />
            </Field>
          </FormRow>
          <FormRow>
            <Field
              name={`${namePrefix}.options.houseLetter`}
              label={
                <FormattedMessage
                  defaultMessage="House letter Schema target"
                  description="'Objects registration variable mapping, addressNL component: 'options.houseLetter schema target' label"
                />
              }
              noManageChildProps
            >
              <TargetPathSelect
                name={`${namePrefix}.options.houseLetter`}
                isLoading={loading}
                targetPaths={stringTypeTargetPaths}
              />
            </Field>
          </FormRow>
          <FormRow>
            <Field
              name={`${namePrefix}.options.houseNumberAddition`}
              label={
                <FormattedMessage
                  defaultMessage="House number addition Schema target"
                  description="Objects registration variable mapping, addressNL component: 'options.houseNumberAddition schema target' label"
                />
              }
              noManageChildProps
            >
              <TargetPathSelect
                name={`${namePrefix}.options.houseNumberAddition`}
                isLoading={loading}
                targetPaths={stringTypeTargetPaths}
              />
            </Field>
          </FormRow>
          <FormRow>
            <Field
              name={`${namePrefix}.options.city`}
              label={
                <FormattedMessage
                  defaultMessage="City Schema target"
                  description="Objects registration variable mapping, addressNL component: 'options.city schema target' label"
                />
              }
              disabled={!deriveAddress}
              noManageChildProps
            >
              <TargetPathSelect
                name={`${namePrefix}.options.city`}
                isLoading={loading}
                targetPaths={stringTypeTargetPaths}
                isDisabled={!deriveAddress}
              />
            </Field>
          </FormRow>
          <FormRow>
            <Field
              name={`${namePrefix}.options.streetName`}
              label={
                <FormattedMessage
                  defaultMessage="Street name Schema target"
                  description="Objects registration variable mapping, addressNL component: 'options.streetName schema target' label"
                />
              }
              disabled={!deriveAddress}
              noManageChildProps
            >
              <TargetPathSelect
                name={`${namePrefix}.options.streetName`}
                isLoading={loading}
                targetPaths={stringTypeTargetPaths}
                isDisabled={!deriveAddress}
              />
            </Field>
          </FormRow>
        </Fieldset>
      )}
      {!specificTargetPaths && (
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
      )}
    </>
  );
};
