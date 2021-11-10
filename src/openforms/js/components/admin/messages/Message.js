import React from 'react';
import PropTypes from 'prop-types';

const KNOWN_TAGS = [
    'debug',
    'info',
    'success',
    'warning',
    'error',
];

const Message = ({ children, tags=[] }) => (
    <li className={tags.join(' ')}>{children}</li>
);

Message.propTypes = {
    children: PropTypes.node.isRequired,
    tags: PropTypes.arrayOf(PropTypes.oneOf(KNOWN_TAGS)),
};


const SuccessMessage = ({ message }) => (<Message tags={['success']}>{children}</Message>);
const WarningMessage = ({ message }) => (<Message tags={['warning']}>{children}</Message>);
const ErrorMessage = ({ message }) => (<Message tags={['error']}>{children}</Message>);
const InfoMessage = ({ message }) => (<Message tags={['info']}>{children}</Message>);


export default Message;
export {
    SuccessMessage,
    WarningMessage,
    ErrorMessage,
    InfoMessage,
}
