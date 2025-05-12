import PropTypes from 'prop-types';

import LoAOverride from '../LoAOverride';
import AdditionalScopesField from './AdditionalScopesField';
import AuthenticationAttributeField from './AuthenticationAttributeField';

const YiviOptionsForm = ({name, plugin, authBackend, onChange}) => {
  const {authenticationAttribute, additionalScopes, loa} = authBackend.options;
  return (
    <>
      <AuthenticationAttributeField
        name={`${name}.options.authenticationAttribute`}
        authenticationAttribute={authenticationAttribute}
        schema={plugin.schema}
        onChange={onChange}
      />
      <AdditionalScopesField
        name={`${name}.options.additionalScopes`}
        additionalScopes={additionalScopes}
        schema={plugin.schema}
        onChange={onChange}
      />
      {authenticationAttribute === 'bsn' && (
        <LoAOverride
          name={`${name}.options.loa`}
          schema={plugin.schema}
          loa={loa}
          onChange={onChange}
        />
      )}
    </>
  );
};

YiviOptionsForm.propType = {
  name: PropTypes.string.isRequired,
  authBackend: PropTypes.shape({
    backend: PropTypes.string.isRequired, // Auth plugin id
    // Options configuration shape is specific to plugin
    options: PropTypes.shape({
      authenticationAttribute: PropTypes.string,
      additionalScopes: PropTypes.arrayOf(PropTypes.string),
      loa: PropTypes.string,
    }),
  }).isRequired,
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
  onChange: PropTypes.func.isRequired,
};

export default YiviOptionsForm;
