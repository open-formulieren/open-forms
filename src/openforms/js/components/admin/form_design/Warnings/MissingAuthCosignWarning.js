import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from 'components/admin/MessageList';
import {FormContext} from 'components/admin/form_design/Context';

const MissingAuthCosignWarning = () => {
  const {selectedAuthPlugins} = useContext(FormContext);

  if (selectedAuthPlugins.length > 0) return null;

  const warning = {
    level: 'warning',
    message: (
      <FormattedMessage
        description="MissingAuthCosignWarning message"
        defaultMessage="The co-sign component requires at least one authentication plugin to be enabled."
      />
    ),
  };

  return <MessageList messages={[warning]} />;
};

MissingAuthCosignWarning.propTypes = {};

export default MissingAuthCosignWarning;
