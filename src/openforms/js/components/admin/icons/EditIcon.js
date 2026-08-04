import PropTypes from 'prop-types';
import React from 'react';

import FAIcon from './FAIcon';

const EditIcon = ({label, onClick}) => (
  <button
    type="button"
    onClick={onClick}
    className="button button--plain actions__action"
    aria-label={label}
    title={label}
  >
    <FAIcon icon="edit" extraClassname="fa-lg" />
  </button>
);

EditIcon.propTypes = {
  label: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default EditIcon;
