import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';
import {getReactSelectOptionsFromSchema} from 'utils/json-schema';

import LoAOverride from '../LoAOverride';

const YiviOptionsFormKvkFields = ({plugin}) => {
  const loaOptions = getReactSelectOptionsFromSchema(
    plugin.schema.properties.kvkLoa.enum,
    plugin.schema.properties.kvkLoa.enumNames,
    '------'
  );

  return (
    <Fieldset
      title={
        <FormattedMessage
          defaultMessage="Yivi plugin options for kvk"
          description="Yivi plugin options for kvk fieldset title"
        />
      }
    >
      <LoAOverride name="kvkLoa" options={loaOptions} />
    </Fieldset>
  );
};

YiviOptionsFormKvkFields.propType = {
  plugin: PropTypes.shape({
    id: PropTypes.string,
    label: PropTypes.string,
    providesAuth: PropTypes.arrayOf(PropTypes.string),
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        kvkLoa: PropTypes.exact({
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

export default YiviOptionsFormKvkFields;
