import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';
import {components} from 'react-select';

import ReactSelect from 'components/admin/forms/ReactSelect';

export const TargetPathType = PropTypes.shape({
  targetPath: PropTypes.arrayOf(PropTypes.string).isRequired,
  isRequired: PropTypes.bool.isRequired,
});

/**
 * (String) representation of a property target, used as dropdown option labels.
 */
export const TargetPathDisplay = ({target}) => {
  const path = target.targetPath.length ? target.targetPath.join(' > ') : '/ (root)';
  return (
    <FormattedMessage
      description="Representation of a JSON Schema target path"
      defaultMessage="{required, select, true {{path} (required)} other {{path}}}"
      values={{path, required: target.isRequired}}
    />
  );
};

TargetPathDisplay.propTypes = {
  target: TargetPathType.isRequired,
};

/**
 * Dropdown that allows you to select a particular (nested) path to a JsonSchema property.
 *
 * The form state must use the key `variablesMapping` for the mapped variables.
 */
const TargetPathSelect = ({
  name,
  isLoading = false,
  targetPaths = [],
  isDisabled = false,
  ...props
}) => {
  // To avoid having an incomplete variable mapping added in the `variablesMapping` array,
  // It is added only when an actual target path is selected. This way, having the empty
  // option selected means the variable is unmapped (hence the `arrayHelpers.remove` call below).
  const {getFieldProps, setFieldValue} = useFormikContext();
  const {value} = getFieldProps(name);

  const options = targetPaths.map(({targetPath, isRequired}) => ({
    value: JSON.stringify(targetPath),
    label: targetPath.length ? targetPath.join(' > ') : '/ (root)',
    targetPath: targetPath,
    isRequired: isRequired,
  }));

  return (
    <ReactSelect
      name={name}
      options={options}
      isLoading={isLoading}
      isDisabled={isDisabled}
      isClearable
      value={value ? options.find(o => o.value === JSON.stringify(value)) : null}
      components={{
        Option: props => (
          <components.Option {...props}>
            <TargetPathDisplay target={props.data} />
          </components.Option>
        ),
      }}
      onChange={newValue => {
        setFieldValue(name, newValue ? newValue.targetPath : undefined);
      }}
      {...props}
    />
  );
};

TargetPathSelect.propTypes = {
  name: PropTypes.string.isRequired,
  isLoading: PropTypes.bool,
  targetPaths: PropTypes.arrayOf(TargetPathType),
  isDisabled: PropTypes.bool,
};

export default TargetPathSelect;
