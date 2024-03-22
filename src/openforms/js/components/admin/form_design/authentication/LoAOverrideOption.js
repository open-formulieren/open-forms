import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

const LoAOverrideOption = ({
  availableAuthPlugins,
  selectedAuthPlugins,
  authenticationBackendOptions,
  onChange,
}) => {
  // These are the selected plugins that support overriding the LoA via the Authentication request
  const pluginsToDisplay = availableAuthPlugins.filter(
    plugin =>
      selectedAuthPlugins.includes(plugin.id) &&
      plugin.supportsLoaOverride &&
      plugin.assuranceLevels.length
  );

  if (pluginsToDisplay.length === 0) return null;

  return (
    <FormRow>
      <Field
        name="form.authenticationBackendOptions"
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
        <ul>
          {pluginsToDisplay.map(plugin => (
            <li key={plugin.id}>
              <label htmlFor={`form.authenticationBackendOptions.${plugin.id}.loa`}>
                {plugin.label}
              </label>
              <Select
                key={plugin.id}
                id={`form.authenticationBackendOptions.${plugin.id}.loa`}
                name={`form.authenticationBackendOptions.${plugin.id}.loa`}
                value={authenticationBackendOptions[plugin.id]?.loa}
                onChange={onChange}
                allowBlank={true}
                choices={plugin.assuranceLevels.map(loa => [loa.value, loa.label])}
              />
            </li>
          ))}
        </ul>
      </Field>
    </FormRow>
  );
};

export default LoAOverrideOption;

LoAOverrideOption.propTypes = {
  onChange: PropTypes.func.isRequired,
  availableAuthPlugins: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      label: PropTypes.string,
      providesAuth: PropTypes.string,
    })
  ).isRequired,
  selectedAuthPlugins: PropTypes.arrayOf(PropTypes.string).isRequired,
  authenticationBackendOptions: PropTypes.object,
};
