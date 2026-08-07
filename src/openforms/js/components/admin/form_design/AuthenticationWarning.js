import {iterComponents} from '@open-formulieren/formio-builder/formio';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from 'components/admin/MessageList';

const CUSTOM_FIELD_TYPES = ['npFamilyMembers'];

const AuthenticationWarning = ({loginRequired, configuration}) => {
  if (loginRequired) return null;

  const componentsWithCustomFieldTypes = [];
  for (const {component} of iterComponents(configuration.components || [])) {
    if (CUSTOM_FIELD_TYPES.includes(component.type)) {
      componentsWithCustomFieldTypes.push(component);
    }
  }

  if (!componentsWithCustomFieldTypes.length) return null;

  const formattedWarnings = componentsWithCustomFieldTypes.map((component, index) => ({
    level: 'warning',
    message: (
      <FormattedMessage
        key={index}
        description="No login required for formstep"
        defaultMessage="Component {label} requires login, but this form step doesn't have the login marked as required."
        values={{label: component.label}}
      />
    ),
  }));

  return <MessageList messages={formattedWarnings} />;
};

AuthenticationWarning.propTypes = {
  loginRequired: PropTypes.bool.isRequired,
  configuration: PropTypes.object.isRequired,
};

export default AuthenticationWarning;
