import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from 'components/admin/MessageList';
import {FormContext} from 'components/admin/form_design/Context';

const MissingAuthCosignWarning = ({cosignComponent}) => {
  const {selectedAuthPlugins, plugins} = useContext(FormContext);

  if (selectedAuthPlugins.includes(cosignComponent.authPlugin)) return null;

  const getAuthPluginLabel = pluginId => {
    for (const plugin of plugins.availableAuthPlugins) {
      if (plugin.id === pluginId) return plugin.label;
    }

    return pluginId;
  };

  const warning = {
    level: 'warning',
    message: (
      <FormattedMessage
        description="MissingAuthCosignWarning message"
        defaultMessage="The the co-sign component requires the {plugin} authentication plugin, but this plugin is not enabled on the form."
        values={{plugin: getAuthPluginLabel(cosignComponent.authPlugin)}}
      />
    ),
  };

  return <MessageList messages={[warning]} />;
};

MissingAuthCosignWarning.propTypes = {
  cosignComponent: PropTypes.object.isRequired,
};

export default MissingAuthCosignWarning;
