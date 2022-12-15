import PropTypes from 'prop-types';
import React from 'react';

const ButtonContainer = ({onClick, children: content}) => {
  return (
    <div className="button-container button-container--padded">
      <button type="button" className="button button--plain" onClick={onClick}>
        <span className="addlink">{content}</span>
      </button>
    </div>
  );
};

ButtonContainer.propTypes = {
  onClick: PropTypes.func.isRequired,
  children: PropTypes.node.isRequired,
};

export default ButtonContainer;
