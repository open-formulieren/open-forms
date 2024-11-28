import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import ButtonContainer from 'components/admin/forms/ButtonContainer';
import {DeleteIcon} from 'components/admin/icons';
import useOnChanged from 'hooks/useOnChanged';

import {Input} from './Inputs';

const ArrayInput = ({
  name,
  inputType,
  values = [],
  onChange,
  deleteConfirmationMessage,
  addButtonMessage,
  wrapEvent = false,
  ...extraProps
}) => {
  const intl = useIntl();

  const [inputs, setInputs] = useState([...values]);

  const onAdd = event => {
    setInputs(inputs.concat(['']));
  };

  const onDelete = index => {
    let modifiedInputs = [...inputs];
    modifiedInputs.splice(index, 1);
    setInputs(modifiedInputs);
  };

  const onInputChange = (index, event) => {
    let modifiedInputs = [...inputs];
    modifiedInputs[index] = event.target.value;
    setInputs(modifiedInputs);
  };

  useOnChanged(inputs, () => {
    const event = wrapEvent ? {target: {name, value: inputs}} : inputs;
    onChange(event);
  });

  return (
    <div className="array-input">
      {inputs.map((value, index) => (
        <div key={index} className="array-input__item">
          <div className="array-input__actions">
            <DeleteIcon
              onConfirm={onDelete.bind(null, index)}
              message={
                deleteConfirmationMessage ||
                intl.formatMessage({
                  description: 'Confirmation message to delete an item from a multi-value input',
                  defaultMessage: 'Are you sure you want to delete this item?',
                })
              }
              icon="times"
            />
          </div>
          <Input
            name={`${name}-${index}`}
            type={inputType}
            value={value}
            onChange={onInputChange.bind(null, index)}
            {...extraProps}
          />
        </div>
      ))}
      <ButtonContainer onClick={onAdd}>
        {addButtonMessage || (
          <FormattedMessage description="Add item to multi-input field" defaultMessage="Add item" />
        )}
      </ButtonContainer>
    </div>
  );
};

ArrayInput.propTypes = {
  name: PropTypes.string.isRequired,
  inputType: PropTypes.string.isRequired,
  values: PropTypes.arrayOf(PropTypes.string),
  onChange: PropTypes.func.isRequired,
  deleteConfirmationMessage: PropTypes.node,
  addButtonMessage: PropTypes.node,
};

export default ArrayInput;
