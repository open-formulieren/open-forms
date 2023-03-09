import produce from 'immer';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import DeleteIcon from 'components/admin/DeleteIcon';
import ButtonContainer from 'components/admin/forms/ButtonContainer';

import ArrayInput from './ArrayInput';
import {Input, TextInput} from './Inputs';

const MappingArrayInput = ({
  inputType,
  mapping,
  onChange,
  deleteConfirmationMessage,
  addButtonMessage,
  valueArrayInput = false,
}) => {
  const intl = useIntl();

  const onAdd = () => {
    const newValue = valueArrayInput ? [''] : '';
    const newMapping = produce(mapping, draft => {
      draft.push(['', newValue]);
    });
    onChange(newMapping);
  };

  const onDelete = index => {
    return produce(mapping, draft => draft.filter((_, itemIndex) => itemIndex !== index));
  };

  const onInputChange = (itemIndex, event) => {
    const {name, value} = event.target;
    const index = {key: 0, value: 1}[name];
    const newMapping = produce(mapping, draft => {
      draft[itemIndex][index] = value;
    });
    onChange(newMapping);
  };

  return (
    <>
      <table className="mapping-array-input">
        <thead className="mapping-array-input">
          <tr>
            <th scope="col" />
            <th scope="col">
              <FormattedMessage
                description="Label for 'key' in MappingArrayInput table column"
                defaultMessage="Key"
              />
            </th>
            <th scope="col">
              <FormattedMessage
                description="Label for 'value' in MappingArrayInput table column"
                defaultMessage="Value"
              />
            </th>
          </tr>
        </thead>
        <tbody>
          {mapping.map(([key, value], index) => (
            <tr key={index} className="mapping-array-input__item">
              <td>
                <div className="mapping-array-input__actions">
                  <DeleteIcon
                    onConfirm={onDelete.bind(null, index)}
                    message={
                      deleteConfirmationMessage ||
                      intl.formatMessage({
                        description:
                          'Confirmation message to delete an item from a multi-value input',
                        defaultMessage: 'Are you sure you want to delete this item?',
                      })
                    }
                    icon="times"
                  />
                </div>
              </td>
              <td>
                <TextInput
                  name="key"
                  value={key}
                  onChange={onInputChange.bind(null, index)}
                  noVTextField
                />
              </td>
              <td>
                {valueArrayInput ? (
                  <ArrayInput
                    name="value"
                    inputType={inputType}
                    key={key}
                    values={value}
                    onChange={onInputChange.bind(null, index)}
                    addButtonMessage={
                      <FormattedMessage
                        description="Label for add button used in MappingArrayInput"
                        defaultMessage="Add another value"
                      />
                    }
                    wrapEvent
                  />
                ) : (
                  <Input
                    type={inputType}
                    name="value"
                    value={value}
                    onChange={onInputChange.bind(null, index)}
                  />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <ButtonContainer onClick={onAdd}>
        {addButtonMessage || (
          <FormattedMessage description="Add item to multi-input field" defaultMessage="Add item" />
        )}
      </ButtonContainer>
    </>
  );
};

MappingArrayInput.propTypes = {
  inputType: PropTypes.string.isRequired,
  mapping: PropTypes.arrayOf(PropTypes.array),
  onChange: PropTypes.func.isRequired,
  deleteConfirmationMessage: PropTypes.node,
  addButtonMessage: PropTypes.node,
};

export default MappingArrayInput;
