import {FieldArray, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import DeleteIcon from 'components/admin/DeleteIcon';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import Select from 'components/admin/forms/Select';
import VariableSelection from 'components/admin/forms/VariableSelection';

const VariableMapping = ({loading, mappingName, formVariables, dmnVariables}) => {
  const intl = useIntl();
  const {getFieldProps, values} = useFormikContext();

  const confirmationMessage = intl.formatMessage({
    description: 'Confirmation message to remove a mapping',
    defaultMessage: 'Are you sure that you want to remove this mapping?',
  });

  return (
    <FieldArray
      name={mappingName}
      render={arrayHelpers => (
        <div className="mappings__mapping-table">
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
              {values[mappingName].map((item, index) => (
                <tr key={index}>
                  <td>
                    <Field
                      name={`${mappingName}.${index}.formVariable`}
                      htmlFor={`${mappingName}.${index}.formVariable`}
                    >
                      <VariableSelection
                        id={`${mappingName}.${index}.formVariable`}
                        {...getFieldProps(`${mappingName}.${index}.formVariable`)}
                        aria-label={intl.formatMessage({
                          description: 'Accessible label for (form) variable dropdown',
                          defaultMessage: 'Form variable',
                        })}
                      />
                    </Field>
                  </td>
                  <td>
                    <Field
                      htmlFor={`${mappingName}.${index}.dmnVariable`}
                      name={`${mappingName}.${index}.dmnVariable`}
                    >
                      <Select
                        id={`${mappingName}.${index}.dmnVariable`}
                        allowBlank
                        disabled={loading}
                        choices={dmnVariables}
                        {...getFieldProps(`${mappingName}.${index}.dmnVariable`)}
                        aria-label={intl.formatMessage({
                          description: 'Accessible label for DMN variable dropdown',
                          defaultMessage: 'DMN variable',
                        })}
                      />
                    </Field>
                  </td>
                  <td>
                    <DeleteIcon
                      onConfirm={() => arrayHelpers.remove(index)}
                      message={confirmationMessage}
                    />
                  </td>
                </tr>
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
  formVariables: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
  dmnVariables: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
};

export default VariableMapping;
