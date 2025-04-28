import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import ArrayInput from 'components/admin/forms/ArrayInput';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';

const OIDCPluginScopes = ({authenticationOidcPluginScopes, availableAuthPlugins, onChange}) => {
  return (
    <div>
      {authenticationOidcPluginScopes.map((pluginScopes, index) => {
        const plugin = availableAuthPlugins.find(plugin => plugin.id === pluginScopes.pluginId);
        return (
          <div key={pluginScopes.pluginId}>
            <FormattedMessage
              tagName="span"
              description="Plugin name"
              defaultMessage="Plugin: {plugin}"
              values={{
                plugin: plugin.label,
              }}
            />
            <ArrayInput
              name={`form.authenticationOidcPluginScopes.${index}.scopes`}
              values={pluginScopes.scopes}
              onChange={onChange}
              inputType="text"
              wrapEvent
            />
          </div>
        );
      })}
    </div>
  );
};

OIDCPluginScopes.propTypes = {
  onChange: PropTypes.func.isRequired,
  availableAuthPlugins: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      label: PropTypes.string,
      providesAuth: PropTypes.string,
    })
  ).isRequired,
  authenticationOidcPluginScopes: PropTypes.arrayOf(
    PropTypes.shape({
      pluginId: PropTypes.string.isRequired,
      scopes: PropTypes.arrayOf(PropTypes.string).isRequired,
    })
  ).isRequired,
};

const OIDCPluginScopesConfiguration = ({
  authenticationOidcPluginScopes,
  availableAuthPlugins,
  onChange,
}) => {
  if (authenticationOidcPluginScopes.length === 0) return null;
  return (
    <FormRow>
      <Field
        name="form.authenticationOidcPluginScopes"
        label={
          <FormattedMessage
            defaultMessage="Authentication scopes"
            description="form.authenticationOidcPluginScopes label"
          />
        }
        helpText={
          <FormattedMessage
            defaultMessage="Additional scopes that should be used with the authentication, besides the bsn and/or kvk scopes."
            description="form.authenticationOidcPluginScopes help text"
          />
        }
      >
        <OIDCPluginScopes
          onChange={onChange}
          authenticationOidcPluginScopes={authenticationOidcPluginScopes}
          availableAuthPlugins={availableAuthPlugins}
        />
      </Field>
    </FormRow>
  );
};

OIDCPluginScopesConfiguration.propTypes = {
  onChange: PropTypes.func.isRequired,
  availableAuthPlugins: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      label: PropTypes.string,
      providesAuth: PropTypes.string,
    })
  ).isRequired,
  authenticationOidcPluginScopes: PropTypes.arrayOf(
    PropTypes.shape({
      pluginId: PropTypes.string.isRequired,
      scopes: PropTypes.arrayOf(PropTypes.string).isRequired,
    })
  ).isRequired,
};

export default OIDCPluginScopesConfiguration;
