import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';

import LoAOverride from '../LoAOverride';

const YiviOptionsFormBsnFields = ({plugin}) => {
  const {
    values: {authenticationAttribute},
  } = useFormikContext();
  if (authenticationAttribute !== 'bsn') {
    return null;
  }

  const schema = plugin.schema.discriminator.mappings[authenticationAttribute];
  return <LoAOverride schema={schema} />;
};

YiviOptionsFormBsnFields.propType = {
  plugin: PropTypes.shape({
    id: PropTypes.string,
    label: PropTypes.string,
    providesAuth: PropTypes.string,
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        authenticationAttribute: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }).isRequired,
        additionalScopes: PropTypes.exact({
          type: PropTypes.oneOf(['array']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          items: PropTypes.exact({
            type: PropTypes.oneOf(['string']).isRequired,
            enum: PropTypes.arrayOf(PropTypes.string).isRequired,
            enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
          }),
        }).isRequired,
      }),
      anyOf: PropTypes.oneOfType([
        PropTypes.shape({
          type: PropTypes.oneOf(['object']).isRequired,
          properties: PropTypes.shape({
            loa: PropTypes.exact({
              type: PropTypes.oneOf(['string']).isRequired,
              title: PropTypes.string.isRequired,
              description: PropTypes.string.isRequired,
              enum: PropTypes.arrayOf(PropTypes.string).isRequired,
              enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
            }),
          }),
        }),
      ]),
      discriminator: PropTypes.shape({
        bsn: PropTypes.shape({
          type: PropTypes.oneOf(['object']).isRequired,
          properties: PropTypes.shape({
            loa: PropTypes.exact({
              type: PropTypes.oneOf(['string']).isRequired,
              title: PropTypes.string.isRequired,
              description: PropTypes.string.isRequired,
              enum: PropTypes.arrayOf(PropTypes.string).isRequired,
              enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
            }),
          }),
        }),
      }),
    }),
  }),
};

export default YiviOptionsFormBsnFields;
