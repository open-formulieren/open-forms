import {Field, FieldArray} from 'formik';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import DeleteIcon from 'components/admin/DeleteIcon';
import Variable from 'components/admin/form_design/variables/types';
import ButtonContainer from 'components/admin/forms/ButtonContainer';

import {EMPTY_OPTION} from './constants';
import {inputValuesType} from './types';

const VariableMapping = ({mappingName, values, formVariables}) => {
  const intl = useIntl();

  const confirmationMessage = intl.formatMessage({
    description: 'Confirmation message to remove a mapping',
    defaultMessage: 'Are you sure that you want to remove this mapping?',
  });

  return (
    <FieldArray
      name={mappingName}
      render={arrayHelpers => (
        <>
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
                <tr>
                  <td key={index}>
                    <Field
                      id={`${mappingName}.${index}.formVar`}
                      name={`${mappingName}.${index}.formVar`}
                      as="select"
                    >
                      {EMPTY_OPTION}
                      {formVariables.map(variable => (
                        <option key={variable.id} value={variable.key}>
                          {variable.label}
                        </option>
                      ))}
                    </Field>
                  </td>
                  <td>
                    <Field
                      id={`${mappingName}.${index}.dmnVar`}
                      name={`${mappingName}.${index}.dmnVar`}
                    ></Field>
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
        </>
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
