import {FieldArray, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import DeleteIcon from 'components/admin/DeleteIcon';
import Variable from 'components/admin/form_design/variables/types';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import {TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';

import {inputValuesType} from './types';

const VariableMapping = ({mappingName, values, formVariables}) => {
  const intl = useIntl();
  const {getFieldProps} = useFormikContext();

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
              {values[mappingName].map((pair, index) => (
                <tr key={index}>
                  <td>
                    <Field
                      name={`${mappingName}.${index}.formVar`}
                      htmlFor={`${mappingName}.${index}.formVar`}
                    >
                      <Select
                        id={`${mappingName}.${index}.formVar`}
                        allowBlank={true}
                        choices={formVariables.map(variable => [variable.key, variable.name])}
                        {...getFieldProps(`${mappingName}.${index}.formVar`)}
                      />
                    </Field>
                  </td>
                  <td>
                    <Field
                      htmlFor={`${mappingName}.${index}.dmnVar`}
                      name={`${mappingName}.${index}.dmnVar`}
                    >
                      <TextInput
                        id={`${mappingName}.${index}.dmnVar`}
                        {...getFieldProps(`${mappingName}.${index}.dmnVar`)}
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
              arrayHelpers.insert(values[mappingName].length, {formVar: '', dmnVar: ''})
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
  mappingName: PropTypes.string,
  values: inputValuesType,
  formVariables: PropTypes.arrayOf(Variable),
};

export default VariableMapping;
