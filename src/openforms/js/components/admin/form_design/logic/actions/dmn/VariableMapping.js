import {FieldArray, useFormikContext} from 'formik';
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
  includeStaticVariables = false,
  dmnVariables,
  alreadyMapped = [],
}) => {
  const intl = useIntl();
  const {getFieldProps} = useFormikContext();

  const confirmationMessage = intl.formatMessage({
    description: 'Confirmation message to remove a mapping',
    defaultMessage: 'Are you sure that you want to remove this mapping?',
  });

  const dmnVariableProps = getFieldProps(`${prefix}.dmnVariable`);

  const dmnVariableChoices = dmnVariables.filter(
    ([value]) => value === dmnVariableProps.value || !alreadyMapped.includes(value)
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
        <Field htmlFor={`${prefix}.dmnVariable`} name={`${prefix}.dmnVariable`}>
          <Select
            id={`${prefix}.dmnVariable`}
            allowBlank
            disabled={loading}
            choices={dmnVariableChoices}
            {...dmnVariableProps}
            aria-label={intl.formatMessage({
              description: 'Accessible label for DMN variable dropdown',
              defaultMessage: 'DMN variable',
            })}
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
  dmnVariables: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)).isRequired,
  onRemove: PropTypes.func.isRequired,
  includeStaticVariables: PropTypes.bool,
  alreadyMapped: PropTypes.arrayOf(PropTypes.string),
};

const VariableMapping = ({
  loading,
  mappingName,
  dmnVariables,
  includeStaticVariables = false,
  alreadyMapped = [],
}) => {
  const {values} = useFormikContext();

  return (
    <FieldArray
      name={mappingName}
      render={arrayHelpers => (
        <div className="logic-dmn__mapping-table">
          <table>
            <thead>
              <tr>
                <th>
                  <FormattedMessage
                    defaultMessage="Open Forms variable"
                    description="Open Forms variable label"
                  />
                </th>
                <th>
                  <FormattedMessage
                    defaultMessage="DMN variable"
                    description="DMN variable label"
                  />
                </th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {values[mappingName].map((_, index) => (
                <VariableMappingRow
                  key={index}
                  prefix={`${mappingName}.${index}`}
                  onRemove={() => arrayHelpers.remove(index)}
                  loading={loading}
                  includeStaticVariables={includeStaticVariables}
                  dmnVariables={dmnVariables}
                  alreadyMapped={alreadyMapped}
                />
              ))}
            </tbody>
          </table>
          <ButtonContainer
            onClick={() =>
              arrayHelpers.insert(values[mappingName].length, {formVariable: '', dmnVariable: ''})
            }
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
  dmnVariables: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
  alreadyMapped: PropTypes.arrayOf(PropTypes.string),
};

export default VariableMapping;
