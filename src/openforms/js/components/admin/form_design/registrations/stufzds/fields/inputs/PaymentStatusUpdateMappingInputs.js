import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import {TextInput} from 'components/admin/forms/Inputs';
import {DeleteIcon} from 'components/admin/icons';
import useOnChanged from 'hooks/useOnChanged';

const PaymentStatusUpdateMappingInputs = ({
  name,
  values = [],
  onChange,
  deleteConfirmationMessage,
  addButtonMessage,
  wrapEvent = false,
}) => {
  const intl = useIntl();
  const [inputGroups, setInputGroups] = useState([...values]);

  const onAdd = event => {
    setInputGroups(
      inputGroups.concat({
        formVariable: '',
        stufName: '',
      })
    );
  };

  const onDelete = index => {
    const modifiedInputGroups = [...inputGroups];
    modifiedInputGroups.splice(index, 1);
    setInputGroups(modifiedInputGroups);
  };

  const onInputChange = (index, event) => {
    const inputNameWithoutIndex = event.target.name.split('-')[0];
    setInputGroups(
      inputGroups.map((value, groupIndex) => {
        if (groupIndex === index) {
          return {...value, [inputNameWithoutIndex]: event.target.value};
        }
        return value;
      })
    );
  };

  useOnChanged(inputGroups, () => {
    const event = wrapEvent ? {target: {name, value: inputGroups}} : inputGroups;
    onChange(event);
  });

  return (
    <>
      <ul className="payment-status-mapping-fields">
        {inputGroups.map(({formVariable, stufName}, index) => (
          <li key={index} className="payment-status-mapping-fields__item">
            <div>
              <Field
                name={`formVariable-${index}`}
                label={
                  <FormattedMessage
                    description="StUF-ZDS registration options 'paymentStatusUpdateMapping formVariable' label"
                    defaultMessage="Form variable"
                  />
                }
                helpText={
                  <FormattedMessage
                    description="StUF-ZDS registration options 'paymentStatusUpdateMapping formVariable' helpText"
                    defaultMessage="The name of the form variable to be mapped"
                  />
                }
              >
                <TextInput
                  type="string"
                  value={formVariable}
                  onChange={onInputChange.bind(null, index)}
                />
              </Field>
              <Field
                name={`stufName-${index}`}
                label={
                  <FormattedMessage
                    description="StUF-ZDS registration options 'paymentStatusUpdateMapping stufName' label"
                    defaultMessage="StUF-ZDS name"
                  />
                }
                helpText={
                  <FormattedMessage
                    description="StUF-ZDS registration options 'paymentStatusUpdateMapping stufName' helpText"
                    defaultMessage="The name in StUF-ZDS to which the form variable should be mapped"
                  />
                }
              >
                <TextInput
                  type="string"
                  value={stufName}
                  onChange={onInputChange.bind(null, index)}
                />
              </Field>
            </div>
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
          </li>
        ))}
      </ul>
      <ButtonContainer onClick={onAdd}>
        {addButtonMessage || (
          <FormattedMessage description="Add item to multi-input field" defaultMessage="Add item" />
        )}
      </ButtonContainer>
    </>
  );
};

PaymentStatusUpdateMappingInputs.propTypes = {
  name: PropTypes.string.isRequired,
  values: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string.isRequired)),
  onChange: PropTypes.func.isRequired,
  deleteConfirmationMessage: PropTypes.node,
  addButtonMessage: PropTypes.node,
  wrapEvent: PropTypes.bool,
};

export default PaymentStatusUpdateMappingInputs;
