import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import {ChangelistTableWrapper, HeadColumn} from '../../../tables';


const ALL_COMPONENTS = [
    {
        type: 'textfield',
        key: 'text1',
        label: 'Textfield 1',
        stepLabel: 'Stap 1',
    },
    {
        type: 'textfield',
        key: 'text2',
        label: 'Textfield 2',
        stepLabel: 'Stap 2',
    },
    {
        type: 'select',
        key: 'select1',
        label: 'Dropdown',
        stepLabel: 'Stap 2',
    },
];


const HeadColumns = () => {
    const intl = useIntl();

    const enabledText = (<FormattedMessage
        description="Manage process vars enabled checkbox column title"
        defaultMessage="Enabled"
    />);
    const enabledHelp = intl.formatMessage({
        description: 'Manage process vars enabled checkbox help text',
        defaultMessage: 'Check to include the field as process variable',
    });

    const componentText = (<FormattedMessage
        description="Manage process vars component column title"
        defaultMessage="Field"
    />);
    const componentHelp = intl.formatMessage({
        description: 'Manage process vars component help text',
        defaultMessage: 'The value of the selected field will be the process variable value.',
    });

    const aliasText = (<FormattedMessage
        description="Manage process vars alias column title"
        defaultMessage="Alias"
    />);
    const aliasHelp = intl.formatMessage({
        description: 'Manage process vars alias help text',
        defaultMessage: 'If desired, you can specify a different process variable name.',
    });

    return (
        <>
            <HeadColumn content={enabledText} title={enabledHelp} />
            <HeadColumn content={componentText} title={componentHelp} />
            <HeadColumn content={aliasText} title={aliasHelp} />
        </>
    );
};


const SelectProcessVariables = ({ onChange }) => {

    return (
        <ChangelistTableWrapper headColumns={<HeadColumns />}>

        </ChangelistTableWrapper>
    );
};

SelectProcessVariables.propTypes = {
    onChange: PropTypes.func.isRequired,
};


export default SelectProcessVariables;
