import {FieldArray, useFormikContext} from 'formik';
import get from 'lodash/get';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import Select from 'components/admin/forms/Select';
import VariableSelection from 'components/admin/forms/VariableSelection';
import {DeleteIcon, WarningIcon} from 'components/admin/icons';

import {detectMappingProblems} from './utils';

const VariableMappingRow = ({
  loading,
  prefix,
  onRemove,
  targets,
  targetsFieldName,
  selectAriaLabel,
  includeStaticVariables = false,
  alreadyMapped = [],
}) => {
  const intl = useIntl();
  const {getFieldProps} = useFormikContext();

  const confirmationMessage = intl.formatMessage({
    description: 'Confirmation message to remove a mapping',
    defaultMessage: 'Are you sure that you want to remove this mapping?',
  });

  const targetsProps = getFieldProps(`${prefix}.${targetsFieldName}`);
  const targetsChoices = targets.filter(
    ([value]) => value === targetsProps.value || !alreadyMapped.includes(value)
  );

  const mapping = getFieldProps(prefix).value;
  const errors = detectMappingProblems(mapping, intl).join(', ');
  return (
    <tr>
      <td>
        <Field name={`${prefix}.formVariable`} htmlFor={`${prefix}.formVariable`}>
          <VariableSelection
            id={`${prefix}.formVariable`}
            includeStaticVariables={includeStaticVariables}
            {...getFieldProps(`${prefix}.formVariable`)}
            aria-label={intl.formatMessage({
              description: 'Accessible label for (form) variable dropdown',
              defaultMessage: 'Form variable',
            })}
          />
        </Field>
      </td>
      <td>
        <Field htmlFor={`${prefix}.${targetsFieldName}`} name={`${prefix}.${targetsFieldName}`}>
          <Select
            id={`${prefix}.${targetsFieldName}`}
            allowBlank
            disabled={loading}
            choices={targetsChoices}
            {...targetsProps}
            aria-label={selectAriaLabel}
          />
        </Field>
      </td>
      <td>
        <DeleteIcon onConfirm={onRemove} message={confirmationMessage} />
        {errors && <WarningIcon text={errors} />}
      </td>
    </tr>
  );
};

VariableMappingRow.propTypes = {
  loading: PropTypes.bool.isRequired,
  prefix: PropTypes.string.isRequired,
  targets: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)).isRequired,
  targetsFieldName: PropTypes.string.isRequired,
  selectAriaLabel: PropTypes.string.isRequired,
  onRemove: PropTypes.func.isRequired,
  includeStaticVariables: PropTypes.bool,
  alreadyMapped: PropTypes.arrayOf(PropTypes.string),
};

const VariableMapping = ({
  loading,
  mappingName,
  targets,
  targetsFieldName,
  targetsColumnLabel,
  selectAriaLabel,
  cssBlockName,
  includeStaticVariables = false,
  alreadyMapped = [],
}) => {
  const {values} = useFormikContext();

  return (
    <FieldArray
      name={mappingName}
      render={arrayHelpers => (
        <div className={`${cssBlockName}__mapping-table`}>
          <table>
            <thead>
              <tr>
                <th>
                  <FormattedMessage
                    defaultMessage="Open Forms variable"
                    description="Open Forms variable label"
                  />
                </th>
                <th>{targetsColumnLabel}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {get(values, mappingName).map((_, index) => (
                <VariableMappingRow
                  key={index}
                  prefix={`${mappingName}.${index}`}
                  onRemove={() => arrayHelpers.remove(index)}
                  loading={loading}
                  includeStaticVariables={includeStaticVariables}
                  targets={targets}
                  targetsFieldName={targetsFieldName}
                  selectAriaLabel={selectAriaLabel}
                  alreadyMapped={alreadyMapped}
                />
              ))}
            </tbody>
          </table>
          <ButtonContainer
            onClick={() => {
              const initial = {formVariable: ''};
              initial[targetsFieldName] = '';
              arrayHelpers.insert(get(values, mappingName).length, initial);
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
  loading: PropTypes.bool,
  mappingName: PropTypes.string,
  includeStaticVariables: PropTypes.bool,
  targets: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
  targetsFieldName: PropTypes.string,
  targetsColumnLabel: PropTypes.string.isRequired,
  selectAriaLabel: PropTypes.string.isRequired,
  cssBlockName: PropTypes.string,
  alreadyMapped: PropTypes.arrayOf(PropTypes.string),
};

export default VariableMapping;
