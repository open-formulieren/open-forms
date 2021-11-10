import React from 'react';
import PropTypes from 'prop-types';


const MessageList = ({ children }) => {
    if (!children) return null;
    return (
        <ul className="messagelist">
            {children}
        </ul>
    );
};

MessageList.propTypes = {
    children: PropTypes.node,
};


export default MessageList;
