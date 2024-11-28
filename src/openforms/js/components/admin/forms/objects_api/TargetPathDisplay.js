import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

const TargetPathDisplay = ({target}) => {
  const path = target.targetPath.length ? target.targetPath.join(' > ') : '/ (root)';
  return (
    <FormattedMessage
      description="Representation of a JSON Schema target path"
      defaultMessage="{required, select, true {{path} (required)} other {{path}}}"
      values={{path, required: target.isRequired}}
    />
  );
};

TargetPathDisplay.propTypes = {
  target: PropTypes.shape({
    targetPath: PropTypes.arrayOf(PropTypes.string).isRequired,
    isRequired: PropTypes.bool.isRequired,
  }).isRequired,
};

export default TargetPathDisplay;
