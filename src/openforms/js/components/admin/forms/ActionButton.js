import React from 'react';
import PropTypes from 'prop-types';
import {useIntl} from 'react-intl';


const ActionButton = ({ text, name='', ...props }) => {
    const extraProps = {...props};
    if (name) {
        extraProps.name = name;
    }
    return (
        <input type="submit" value={text} {...extraProps} />
    );
};

ActionButton.propTypes = {
    text: PropTypes.string.isRequired,
    name: PropTypes.string,
};


const SubmitAction = (props) => {
    const intl = useIntl();
    const btnText = intl.formatMessage({
        description: 'Admin save submit button',
        defaultMessage: 'Save',
    });
    return (<ActionButton name="_save" text={btnText} {...props} />);
};


const AddAnotherAction = (props) => {
    const intl = useIntl();
    const btnText = intl.formatMessage({
        description: 'Admin save and add another submit button',
        defaultMessage: 'Save and add another',
    });
    return (<ActionButton name="_addanother" text={btnText} {...props} />);
};


const ContinueEditingAction = (props) => {
    const intl = useIntl();
    const btnText = intl.formatMessage({
        description: 'Admin save and continue editing submit button',
        defaultMessage: 'Save and continue editing',
    });
    return (<ActionButton name="_continue" text={btnText} {...props} />);
};


export default ActionButton;
export {ActionButton, SubmitAction, AddAnotherAction, ContinueEditingAction};
