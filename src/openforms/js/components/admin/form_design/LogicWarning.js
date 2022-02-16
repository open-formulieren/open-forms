import React from 'react';
import {FormattedMessage} from 'react-intl';
import PropTypes from 'prop-types';
import MessageList from './warnings/MessageList';



const LogicWarning = ({warnings}) => {
    if (!warnings.length) return null;

    const formattedWarnings = warnings.map((warning, index) => (
        <FormattedMessage
            key={index}
            description="Wrong simple logic warning"
            defaultMessage="Component {label} ({key}) uses a non-existent component key {missingKey} in the simple logic."
            values={{label: warning.component.label, key: warning.component.key, missingKey: warning.missingKey  }}
        />
    ));

    return (<MessageList warnings={formattedWarnings}/>);
};


LogicWarning.propTypes = {
    warnings: PropTypes.arrayOf(PropTypes.object),
};


export default LogicWarning;
