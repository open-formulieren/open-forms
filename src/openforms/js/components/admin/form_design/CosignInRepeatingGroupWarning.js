import React from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from 'components/admin/MessageList';

const CosignInRepeatingGroupWarning = ({cosignComponents, availableComponents}) => {
  if (!cosignComponents) return null;

  let componentInEditgrid = false;
  for (const componentPath in cosignComponents) {
    // components/cosignComponents are dictionaries where the key is the 'path' of the component. For example, for a component 'foo' in a
    // repeating group 'bar', the key is 'bar.foo'.
    const pathBits = componentPath.split('.');
    const numberOfParentsBits = pathBits.length - 1;

    // Check each parent to see if they are editgrids (repeating groups)
    for (let counter = numberOfParentsBits; counter > 0; counter--) {
      const parentPathBits = pathBits.slice(0, counter);
      if (!parentPathBits.length) continue;

      const parentPath = parentPathBits.join('.');
      if (availableComponents[parentPath] && availableComponents[parentPath].type === 'editgrid') {
        componentInEditgrid = true;
        break;
      }
    }
  }

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

export default CosignInRepeatingGroupWarning;
