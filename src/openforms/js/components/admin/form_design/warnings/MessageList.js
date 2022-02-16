import React from 'react';

const MessageList = ({warnings}) => {

    return (
        <ul className="messagelist">
            {
                warnings.map((child, index) => {
                    return (
                        <li key={index} className="warning">{child}</li>
                    );
                })
            }
        </ul>
    );
};

export default MessageList;
