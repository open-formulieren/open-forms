import PropTypes from 'prop-types';

import LoAOverride from '../LoAOverride';
import AdditionalScopesField from './AdditionalScopesField';
import AuthenticationAttributeField from './AuthenticationAttributeField';

const YiviBsnOptionsFields = ({name, plugin, authBackend, onChange}) => {
  const {authenticationAttribute, loa} = authBackend.options;
  const schema = plugin.schema.discriminator.mappings[authenticationAttribute];

  return <LoAOverride name={`${name}.options.loa`} schema={schema} loa={loa} onChange={onChange} />;
};

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
        <YiviBsnOptionsFields
          name={name}
          plugin={plugin}
          authBackend={authBackend}
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
  onChange: PropTypes.func.isRequired,
};

export default YiviOptionsForm;
