import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from '../MessageList';

const MultipleCosignComponentsWarning = ({components}) => {
  const coSignComponents = Object.entries(components).filter(
    ([key, component]) => component.type === 'cosign'
  );

  if (coSignComponents.length <= 1) return null;

  const warning = {
    level: 'warning',
    message: (
      <FormattedMessage
        description="Too many cosign components"
        defaultMessage="There are multiple co-sign components specified in this form. At most one should be present."
      />
    ),
  };

  return <MessageList messages={[warning]} />;
};

MultipleCosignComponentsWarning.propTypes = {
  components: PropTypes.objectOf(PropTypes.object).isRequired,
};

export default MultipleCosignComponentsWarning;
