import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';

import Select, {SelectChoicesType} from 'components/admin/forms/Select';

const AttributeField = ({prefillAttributes}) => {
  const [fieldProps] = useField('attribute');
  const {
    values: {plugin},
  } = useFormikContext();

  return (
    <Select
      allowBlank
      choices={prefillAttributes}
      id="id_attribute"
      disabled={!plugin}
      {...fieldProps}
    />
  );
};

AttributeField.propTypes = {
  prefillAttributes: SelectChoicesType.isRequired,
};

export default AttributeField;
