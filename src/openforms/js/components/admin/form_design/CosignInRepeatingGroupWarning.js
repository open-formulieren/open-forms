import FormioUtils from 'formiojs/utils';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from '../MessageList';

const CosignInRepeatingGroupWarning = ({formSteps}) => {
  // Iterate to see if there are repeating groups or co-sign components
  let editGrids = [];
  const cosignComponents = [];
  formSteps.map(step =>
    FormioUtils.eachComponent(step.configuration.components, configComponent => {
      if (configComponent.type === 'editgrid') {
        editGrids.push(configComponent);
      } else if (configComponent.type === 'cosign') {
        cosignComponents.push(configComponent);
      }
    })
  );

  if (!cosignComponents.length) return null;

  // Check if the co-sign components are in the editgrid
  let foundComponent = false;
  for (const cosignComponent of cosignComponents) {
    for (const editGrid of editGrids) {
      foundComponent = FormioUtils.getComponent(editGrid.components, cosignComponent.key, true);
      if (foundComponent) break;
    }
  }

  if (!foundComponent) return null;

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
