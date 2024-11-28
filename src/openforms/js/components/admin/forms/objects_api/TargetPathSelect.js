import {FieldArray, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React from 'react';

import Select from 'components/admin/forms/Select';

const TargetPathSelect = ({name, index, choices, mappedVariable, disabled}) => {
  // To avoid having an incomplete variable mapping added in the `variablesMapping` array,
  // It is added only when an actual target path is selected. This way, having the empty
  // option selected means the variable is unmapped (hence the `arrayHelpers.remove` call below).
  const {
    values: {variablesMapping},
    getFieldProps,
    setFieldValue,
  } = useFormikContext();
  const props = getFieldProps(name);
  const isNew = !!variablesMapping ? variablesMapping.length === index : false;
  return (
    <FieldArray
      name="variablesMapping"
      render={arrayHelpers => (
        <Select
          id="targetPath"
          name={name}
          allowBlank
          choices={choices}
          {...props}
          disabled={disabled}
          value={JSON.stringify(props.value)}
          onChange={event => {
            if (event.target.value === '') {
              arrayHelpers.remove(index);
            } else {
              if (isNew) {
                arrayHelpers.push({...mappedVariable, targetPath: JSON.parse(event.target.value)});
              } else {
                setFieldValue(name, JSON.parse(event.target.value));
              }
            }
          }}
        />
      )}
    />
  );
};

TargetPathSelect.propTypes = {
  name: PropTypes.string.isRequired,
  index: PropTypes.number.isRequired,
  choices: PropTypes.array.isRequired,
  mappedVariable: PropTypes.object,
};

export default TargetPathSelect;
