import React from 'react';
import PropTypes from 'prop-types';


const ButtonContainer = ({ onClick, children: content }) => {
    return (
        <div className="button-container button-container--padded">
            <button
                type="button"
                className="button button--plain"
                onClick={onClick}
            >
                <span className="addlink">
                    {content}
                </span>
            </button>
        </div>
    );
};

ButtonContainer.propTypes = {
    onClick: PropTypes.func.isRequired,
    children: PropTypes.node.isRequired,
};


export default ButtonContainer;
