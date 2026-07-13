import {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FAIcon} from 'components/admin/icons';

import LiteralValueInput, {CheckboxChoices} from './LiteralValueInput';

// Component-specific overrides
const COMPONENT_TYPE_TO_INPUT_TYPE = {
  // The selectboxes is of type object, so a JSON widget would be used. However, we only need to
  // provide the possibility to select true/false.
  selectboxes: CheckboxChoices,
};

const DefaultValueSelection = ({name, dataType, componentType, value, onChange}) => {
  // If the value is not undefined, it means it was already specified, so we should show the input
  // field.
  const [showInputField, setShowInputField] = useState(value !== undefined);
  const intl = useIntl();

  const onAddDefaultValue = () => {
    onChange({
      target: {
        name: name,
        value: '',
      },
    });
    setShowInputField(true);
  };

  const onRemoveDefaultValue = () => {
    onChange({
      target: {
        name: name,
        value: undefined,
      },
    });
    setShowInputField(false);
  };

  return showInputField ? (
    <div className="default-value-input-container">
      <FormattedMessage description="Default value input label" defaultMessage="Default value:" />
      <LiteralValueInput
        name={name}
        type={dataType}
        componentType={componentType}
        inputTypeOverrides={COMPONENT_TYPE_TO_INPUT_TYPE}
        value={value}
        onChange={onChange}
      />
      <FAIcon
        icon="xmark"
        extraClassname="icon actions__action"
        onClick={onRemoveDefaultValue}
        title={intl.formatMessage({
          description: 'Remove default value icon title',
          defaultMessage: 'Remove default value',
        })}
      />
    </div>
  ) : (
    <button
      name={name}
      type="button"
      className="button default-value-button"
      onClick={onAddDefaultValue}
    >
      <FAIcon icon="plus" />
      <FormattedMessage
        description="Add default value button text"
        defaultMessage="Default value"
      />
    </button>
  );
};

DefaultValueSelection.propTypes = {};

export default DefaultValueSelection;
