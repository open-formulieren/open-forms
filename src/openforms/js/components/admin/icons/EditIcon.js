import PropTypes from 'prop-types';
import React from 'react';

import FAIcon from './FAIcon';

const EditIcon = ({label, onClick}) => (
  <FAIcon
    icon="edit"
    extraClassname="fa-lg actions__action"
    accessibleLabel={label}
    onClick={onClick}
  />
);

EditIcon.propTypes = {
  label: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default EditIcon;
