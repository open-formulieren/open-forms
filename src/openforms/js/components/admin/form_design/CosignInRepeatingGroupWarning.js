import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from 'components/admin/MessageList';

const CosignInRepeatingGroupWarning = ({cosignComponents, availableComponents}) => {
  if (!Object.keys(cosignComponents).length) return null;

  // In cosignComponents the key is the 'path' of the component. For example, for a component 'foo' in a
  // repeating group 'bar', the key is 'bar.foo'.
  const isInEditGrid = pathParts => {
    const path = pathParts.join('.');
    if (!path) return false; // reached root
    if (availableComponents[path] && availableComponents[path].type === 'editgrid') return true;
    return isInEditGrid(pathParts.slice(0, -1)); // check parent
  };

  const componentInEditgrid = Object.keys(cosignComponents).some(path =>
    isInEditGrid(path.split('.'))
  );
  if (!componentInEditgrid) return null;

  const warning = {
    level: 'warning',
    message: (
      <FormattedMessage
        description="Cosign components in repeating group warning message"
        defaultMessage="There are co-sign components inside repeating groups. This is not supported."
      />
    ),
  };

  return <MessageList messages={[warning]} />;
};

CosignInRepeatingGroupWarning.propTypes = {
  cosignComponents: PropTypes.objectOf(PropTypes.object).isRequired,
  availableComponents: PropTypes.objectOf(PropTypes.object).isRequired,
};

export default CosignInRepeatingGroupWarning;
