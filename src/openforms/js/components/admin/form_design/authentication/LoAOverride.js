import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {getReactSelectOptionsFromSchema} from 'utils/json-schema';

const LoAOverride = ({schema}) => {
  const LoaOptions = getReactSelectOptionsFromSchema(
    schema.properties.loa.enum,
    schema.properties.loa.enumNames,
    '------'
  );
  return (
    <FormRow>
      <Field
        name="loa"
        label={
          <FormattedMessage
            description="Minimal levels of assurance label"
            defaultMessage="Minimal levels of assurance"
          />
        }
        helpText={
          <FormattedMessage
            defaultMessage="Override the minimum Level of Assurance. This is not supported by all authentication plugins."
            description="Minimal LoA override help text"
          />
        }
      >
        <ReactSelect name="loa" options={LoaOptions} />
      </Field>
    </FormRow>
  );
};

LoAOverride.propTypes = {
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']).isRequired,
    properties: PropTypes.shape({
      loa: PropTypes.exact({
        type: PropTypes.oneOf(['string']).isRequired,
        title: PropTypes.string.isRequired,
        description: PropTypes.string.isRequired,
        enum: PropTypes.arrayOf(PropTypes.string).isRequired,
        enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
      }).isRequired,
    }),
  }).isRequired,
};

export default LoAOverride;
