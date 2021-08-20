import React from 'react';
import PropTypes from 'prop-types';
import {useIntl} from 'react-intl';

import FAIcon from './FAIcon';


const DeleteIcon = ({ onConfirm, message }) => {
    const intl = useIntl();
    const defaultMessage = intl.formatMessage({
        description: 'Default delete confirmation message',
        defaultMessage: 'Are you sure you want to delete this?',
    });
    const confirmMessage = message || defaultMessage;

    const iconTitle = intl.formatMessage({
        description: 'Delete icon title',
        defaultMessage: 'Delete',
    });

    const onClick = () => {
        if (window.confirm(confirmMessage)) {
            onConfirm();
        }
    };

    return (
        <FAIcon
            icon="trash"
            extraClassname="icon icon--danger actions__action"
            title={iconTitle}
            onClick={onClick}
        />
    );
};

DeleteIcon.propTypes = {
    onConfirm: PropTypes.func.isRequired,
    message: PropTypes.string,
};


export default DeleteIcon;
