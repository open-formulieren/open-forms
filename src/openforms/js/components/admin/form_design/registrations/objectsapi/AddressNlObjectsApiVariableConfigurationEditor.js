import {FieldArray, useFormikContext} from 'formik';
import isEqual from 'lodash/isEqual';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync, useToggle} from 'react-use';

import {APIContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';
import Select, {LOADING_OPTION} from 'components/admin/forms/Select';
import {TargetPathDisplay} from 'components/admin/forms/objects_api';
import ErrorMessage from 'components/errors/ErrorMessage';
import {post} from 'utils/fetch';

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
  const {values, setFieldValue} = useFormikContext();
  const [jsonSchemaVisible, toggleJsonSchemaVisible] = useToggle(false);
  const {specificTargetPaths} = values;
  const isSpecificTargetPaths =
    specificTargetPaths ||
    (mappedVariable.options && Object.keys(mappedVariable.options).length > 0);

  const deriveAddress = components[variable?.key]['deriveAddress'];

  // // Load all the possible target paths (obect,string and number types) in parallel and only once
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

  const choicesTypes = {
    object: objectTypeTargetPaths,
    string: stringTypeTargetPaths,
    number: numberTypeTargetPaths,
  };

  const getChoices = type =>
    loading || error
      ? LOADING_OPTION
      : choicesTypes[type].map(t => [
          JSON.stringify(t.targetPath),
          <TargetPathDisplay target={t} />,
        ]);

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
    setFieldValue('specificTargetPaths', event.target.checked);

    if (event.target.checked) {
      setFieldValue(`${namePrefix}.targetPath`, undefined);
    } else {
      setFieldValue(`${namePrefix}.options.postcode`, undefined);
      setFieldValue(`${namePrefix}.options.houseLetter`, undefined);
      setFieldValue(`${namePrefix}.options.houseNumber`, undefined);
      setFieldValue(`${namePrefix}.options.houseNumberAddition`, undefined);
      setFieldValue(`${namePrefix}.options.city`, undefined);
      setFieldValue(`${namePrefix}.options.streetName`, undefined);
    }
  };

  return (
    <>
      <FormRow>
        <Field name="specificTargetPaths" disabled={!!mappedVariable.targetPath}>
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
            checked={isSpecificTargetPaths}
            onChange={onSpecificTargetPathsChange}
          />
        </Field>
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
          disabled={isSpecificTargetPaths}
        >
          <TargetPathSelect
            name={`${namePrefix}.targetPath`}
            index={index}
            choices={getChoices('object')}
            mappedVariable={mappedVariable}
            disabled={isGeometry || isSpecificTargetPaths}
          />
        </Field>
      </FormRow>
      {isSpecificTargetPaths && (
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
            >
              <TargetPathSelect
                id="postcode"
                name={`${namePrefix}.options.postcode`}
                index={index}
                choices={getChoices('string')}
                mappedVariable={mappedVariable}
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
            >
              <TargetPathSelect
                id="houseNumber"
                name={`${namePrefix}.options.houseNumber`}
                index={index}
                choices={getChoices('number')}
                mappedVariable={mappedVariable}
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
            >
              <TargetPathSelect
                id="houseLetter"
                name={`${namePrefix}.options.houseLetter`}
                index={index}
                choices={getChoices('string')}
                mappedVariable={mappedVariable}
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
            >
              <TargetPathSelect
                id="houseNumberAddition"
                name={`${namePrefix}.options.houseNumberAddition`}
                index={index}
                choices={getChoices('string')}
                mappedVariable={mappedVariable}
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
            >
              <TargetPathSelect
                id="city"
                name={`${namePrefix}.options.city`}
                index={index}
                choices={getChoices('string')}
                mappedVariable={mappedVariable}
                disabled={!deriveAddress}
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
            >
              <TargetPathSelect
                id="streetName"
                name={`${namePrefix}.options.streetName`}
                index={index}
                choices={getChoices('string')}
                mappedVariable={mappedVariable}
                disabled={!deriveAddress}
              />
            </Field>
          </FormRow>
        </Fieldset>
      )}
      {!isSpecificTargetPaths && (
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

const TargetPathSelect = ({id, name, index, choices, mappedVariable, disabled}) => {
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
          id={id}
          name={name}
          allowBlank
          choices={choices}
          {...props}
          disabled={disabled}
          value={JSON.stringify(props.value)}
          onChange={event => {
            if (event.target.value === '') {
              arrayHelpers.remove(name);
            } else {
              if (isNew) {
                if (name.split('.').pop() in ADDRESSNL_NESTED_PROPERTIES) {
                  arrayHelpers.push({
                    ...mappedVariable,
                    options: {[name.split('.').pop()]: event.target.value},
                  });
                } else {
                  arrayHelpers.push({...mappedVariable});
                }
              }
              setFieldValue(name, JSON.parse(event.target.value));
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
