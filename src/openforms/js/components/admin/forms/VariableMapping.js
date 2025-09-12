import {FieldArray, useFormikContext} from 'formik';
import get from 'lodash/get';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import Select from 'components/admin/forms/Select';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import VariableSelection from 'components/admin/forms/VariableSelection';
import {DeleteIcon, WarningIcon} from 'components/admin/icons';

export const serializeValue = value => JSON.stringify(value);
export const deserializeValue = value => JSON.parse(value);

const LabelType = PropTypes.oneOfType([PropTypes.string, PropTypes.element]);

const isChoice = (props, propName, componentName, location, propFullName) => {
  const prop = props[propName];
  if (!Array.isArray(prop) || prop.length !== 2) {
    return new Error(`Invalid choice (index ${propName} passed to '${componentName}'.
      Each choice must be an array of length 2.`);
  }

  const [value, label] = prop;
  const error = PropTypes.checkPropTypes(
    {value: PropTypes.any, label: LabelType.isRequired},
    {value, label},
    location,
    componentName
  );
  if (error) {
    return error;
  }
  return null;
};

const VariableMappingRow = ({
  prefix,
  loading,
  directionIcon,
  variableName,
  propertyName,
  propertyChoices,
  translatePropertyChoices,
  propertySelectLabel,
  onRemove,
  includeStaticVariables = false,
  alreadyMapped = [],
  rowCheck = undefined,
  errors = undefined,
}) => {
  const intl = useIntl();
  const {getFieldProps, setFieldValue} = useFormikContext();

  const fullVariableName = `${prefix}.${variableName}`;
  const fullPropertyName = `${prefix}.${propertyName}`;
  const {value: propertyValue, ...propertyProps} = getFieldProps(fullPropertyName);
  const serializedPropertyValue = serializeValue(propertyValue);

  // filter out the already mapped values
  propertyChoices = propertyChoices.filter(
    ([serializedValue]) =>
      serializedValue === serializedPropertyValue || !alreadyMapped.includes(serializedValue)
  );

  const mapping = getFieldProps(prefix).value;
  const rowErrors = rowCheck?.(intl, mapping).join(', ') ?? '';
  const variableError = errors?.[variableName];
  const propertyError = errors?.[propertyName];

  return (
    <tr>
      <td>
        <Field name={fullVariableName} errors={variableError}>
          <VariableSelection
            includeStaticVariables={includeStaticVariables}
            {...getFieldProps(fullVariableName)}
            aria-label={intl.formatMessage({
              description: 'Accessible label for (form) variable dropdown',
              defaultMessage: 'Form variable',
            })}
          />
        </Field>
      </td>

      {directionIcon && <td className="mapping-table__direction-icon">{directionIcon}</td>}

      <td>
        <Field name={fullPropertyName} errors={propertyError}>
          <Select
            allowBlank
            disabled={loading}
            choices={propertyChoices}
            translateChoices={translatePropertyChoices}
            {...propertyProps}
            value={serializedPropertyValue}
            onChange={event => {
              let {value} = event.target;
              // empty string means the select was cleared/reset
              if (value === '') value = undefined;
              if (value !== undefined) {
                value = deserializeValue(value);
              }
              setFieldValue(fullPropertyName, value);
            }}
            aria-label={propertySelectLabel}
          />
        </Field>
      </td>

      <td>
        <DeleteIcon
          onConfirm={onRemove}
          message={intl.formatMessage({
            description: 'Confirmation message to remove a mapping',
            defaultMessage: 'Are you sure that you want to remove this mapping?',
          })}
        />
        {rowErrors && <WarningIcon text={rowErrors} />}
      </td>
    </tr>
  );
};

VariableMappingRow.propTypes = {
  /**
   * Prefix for the nested fields ($variableName, $propertyName) to its parent. Used to
   * build the fully qualified names of individual form fields.
   */
  prefix: PropTypes.string.isRequired,

  /**
   * Indicates whether the options are still loading.
   */
  loading: PropTypes.bool.isRequired,

  /**
   * Optional (icon) node to display between the form variable and other property columns.
   *
   * Recommended, since it can help clarify the direction of the mapping.
   */
  directionIcon: PropTypes.node,

  /**
   * Name of the property nested inside each mapping item.
   *
   * This is the property that will be mapped to/from the form variable.
   */
  propertyName: PropTypes.string.isRequired,

  /**
   * Array of possible choices, where each item is a `[value, label]` tuple. The value
   * must already be serialized to a string.
   */
  propertyChoices: PropTypes.arrayOf(isChoice),

  /**
   * Indicates if choices is a translatable object
   */
  translateChoices: PropTypes.bool,

  /**
   * The accessible label for the property dropdown.
   */
  propertySelectLabel: PropTypes.string.isRequired,
  onRemove: PropTypes.func.isRequired,

  /**
   * Name of the variable nested inside each mapping item.
   *
   * This is the form variable to which the property will be mapped.
   */
  variableName: PropTypes.string.isRequired,

  /**
   * Indicates if static variables can be selected for the mapping or not. Assigning
   * to static variables is not possible, but reading from them and assigning the value
   * to a property is possible.
   */
  includeStaticVariables: PropTypes.bool,
  /**
   * Array of values that are already selected in (other) rows, in serialized form.
   */
  alreadyMapped: PropTypes.arrayOf(PropTypes.string),

  /**
   * Optional callback function to check an individual row for problems.
   *
   * The callback will be invoked with `rowCheck(intl, row)` and must return an array
   * of error messages, where `intl` is the context from react-intl's `useIntl()` hook.
   */
  rowCheck: PropTypes.func,

  /**
   * Validation errors from context
   */
  errors: PropTypes.objectOf(PropTypes.string),
};

/**
 * Map form variables to other properties.
 *
 * The form context is used to provide choices for the form variables to map to or from.
 *
 * The `propertyChoices` prop provides the choices for the properties to map from/to,
 * and must be provided when using this component.
 */
const VariableMapping = ({
  name,
  loading,
  directionIcon,
  variableName = 'formVariable',
  propertyName,
  propertyChoices,
  translatePropertyChoices = False,
  propertyHeading,
  propertySelectLabel,
  includeStaticVariables = false,
  rowCheck,
}) => {
  const {values, getFieldProps} = useFormikContext();
  const {value: mappings = []} = getFieldProps(name);
  // normalize all choices by JSON serializing the values
  propertyChoices = propertyChoices.map(([value, label]) => [serializeValue(value), label]);

  // grab the already mapped properties from the formik state
  const alreadyMapped = mappings.map(row => serializeValue(row[propertyName]));

  const errors = Object.fromEntries(useContext(ValidationErrorContext));
  const relatedErrors = errors?.[name];
  return (
    <FieldArray
      name={name}
      render={arrayHelpers => (
        <div className={'mapping-table'}>
          <table>
            <thead>
              <tr>
                <th>
                  <FormattedMessage
                    defaultMessage="Open Forms variable"
                    description="Open Forms variable label"
                  />
                </th>
                {directionIcon && <th />}
                <th>{propertyHeading}</th>
                <th />
              </tr>
            </thead>

            <tbody>
              {mappings.map((_, index) => (
                <VariableMappingRow
                  key={index}
                  prefix={`${name}.${index}`}
                  directionIcon={directionIcon}
                  onRemove={() => arrayHelpers.remove(index)}
                  loading={loading}
                  includeStaticVariables={includeStaticVariables}
                  propertyChoices={propertyChoices}
                  translatePropertyChoices={translatePropertyChoices}
                  variableName={variableName}
                  propertyName={propertyName}
                  propertySelectLabel={propertySelectLabel}
                  alreadyMapped={alreadyMapped}
                  rowCheck={rowCheck}
                  errors={relatedErrors?.[index]}
                />
              ))}
            </tbody>
          </table>

          <ButtonContainer
            onClick={() => {
              // TODO update
              const initial = {[variableName]: '', [propertyName]: ''};
              const mapping = get(values, name) || [];
              arrayHelpers.insert(mapping.length, initial);
            }}
          >
            <FormattedMessage description="Add variable button" defaultMessage="Add variable" />
          </ButtonContainer>
        </div>
      )}
    />
  );
};

VariableMapping.propTypes = {
  /**
   * Dotted path describing the name in the form data of the array with the mappings.
   *
   * This is passed to Formik to manage the nested fields inside.
   */
  name: PropTypes.string,

  /**
   * Indicates whether the options are still loading.
   */
  loading: PropTypes.bool,

  /**
   * Optional (icon) node to display between the form variable and other property columns.
   *
   * Recommended, since it can help clarify the direction of the mapping.
   */
  directionIcon: PropTypes.node,

  /**
   * Name of the variable nested inside each mapping item.
   *
   * This is the form variable to which the property will be mapped.
   */
  variableName: PropTypes.string.isRequired,

  /**
   * Name of the property nested inside each mapping item.
   *
   * This is the property that will be mapped to/from the form variable.
   */
  propertyName: PropTypes.string.isRequired,

  /**
   * Available choices for the mapped variable.
   *
   * Should be an array of `[value, label]` pairs, where each value must be
   * JSON-serializable and the label is a string or react-intl formatted message.
   */
  propertyChoices: PropTypes.arrayOf(isChoice),

  /**
   * Indicates if choices is a translatable object
   */
  translateChoices: PropTypes.bool,

  /**
   * Heading/label for the property column displaying the property choices.
   */
  propertyHeading: PropTypes.node.isRequired,

  /**
   * The accessible label for the property dropdown.
   */
  propertySelectLabel: PropTypes.string.isRequired,

  /**
   * Indicates if static variables can be selected for the mapping or not. Assigning
   * to static variables is not possible, but reading from them and assigning the value
   * to a property is possible.
   */
  includeStaticVariables: PropTypes.bool,

  /**
   * Optional callback function to check an individual row for problems.
   *
   * The callback will be invoked with `rowCheck(intl, row)` and must return an array
   * of error messages, where `intl` is the context from react-intl's `useIntl()` hook.
   */
  rowCheck: PropTypes.func,
};

export default VariableMapping;
