import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';

import OIDCPluginClaimsMapping from './OIDCPluginClaimsMapping';

const OIDCPluginClaimsConfiguration = ({
  authenticationOidcPluginClaims,
  availableAuthPlugins,
  onChange,
}) => {
  if (authenticationOidcPluginClaims.length === 0) return null;
  return (
    <FormRow>
      <Field
        name="form.authenticationOidcPluginClaims"
        label={
          <FormattedMessage
            defaultMessage="Authentication claims mapping"
            description="form.authenticationOidcPluginClaims label"
          />
        }
        helpText={
          <FormattedMessage
            defaultMessage="Additional claims that should be fetched after authentication, besides the bsn and/or kvk claims."
            description="form.authenticationOidcPluginClaims help text"
          />
        }
      >
        <div>
          {authenticationOidcPluginClaims.map((pluginClaims, index) => (
            <OIDCPluginClaimsMapping
              key={index}
              prefix={`form.authenticationOidcPluginClaims.${index}`}
              pluginClaims={pluginClaims}
              availableAuthPlugins={availableAuthPlugins}
              onChange={onChange}
            />
          ))}
        </div>
      </Field>
    </FormRow>
  );
};

OIDCPluginClaimsConfiguration.propTypes = {
  onChange: PropTypes.func.isRequired,
  availableAuthPlugins: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      label: PropTypes.string,
      providesAuth: PropTypes.string,
    })
  ).isRequired,
  authenticationOidcPluginClaims: PropTypes.arrayOf(
    PropTypes.shape({
      pluginId: PropTypes.string.isRequired,
      claimMapping: PropTypes.arrayOf(
        PropTypes.shape({
          claimName: PropTypes.string.isRequired,
          formVariable: PropTypes.string.isRequired,
        })
      ).isRequired,
    })
  ).isRequired,
};

export default OIDCPluginClaimsConfiguration;
