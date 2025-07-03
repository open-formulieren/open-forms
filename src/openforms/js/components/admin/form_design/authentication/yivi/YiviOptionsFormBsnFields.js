import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';
import {getReactSelectOptionsFromSchema} from 'utils/json-schema';

import LoAOverride from '../LoAOverride';

const YiviOptionsFormBsnFields = ({plugin}) => {
  const loaOptions = getReactSelectOptionsFromSchema(
    plugin.schema.properties.bsnLoa.enum,
    plugin.schema.properties.bsnLoa.enumNames,
    '------'
  );

  return (
    <Fieldset
      title={
        <FormattedMessage
          defaultMessage="Yivi plugin options for bsn"
          description="Yivi plugin options for bsn fieldset title"
        />
      }
    >
      <LoAOverride name="bsnLoa" options={loaOptions} />
    </Fieldset>
  );
};

YiviOptionsFormBsnFields.propType = {
  plugin: PropTypes.shape({
    id: PropTypes.string,
    label: PropTypes.string,
    providesAuth: PropTypes.arrayOf(PropTypes.string),
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        bsnLoa: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }).isRequired,
      }),
    }),
  }),
};

export default YiviOptionsFormBsnFields;
