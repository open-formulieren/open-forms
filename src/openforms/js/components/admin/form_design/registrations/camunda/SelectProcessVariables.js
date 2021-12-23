import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import {Checkbox, TextInput} from '../../../forms/Inputs';
import ComponentSelection from '../../../forms/ComponentSelection';
import {ChangelistTableWrapper, HeadColumn, TableRow} from '../../../tables';


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


const ProcessVariable = ({ index, enabled=true, componentKey='', alias='' }) => {

    const onChange = (event) => {
        const {name, value} = event.target;
        console.log(name, value);
    };

    return (
        <TableRow index={index}>
            <Checkbox name="enabled" label="" onChange={onChange} checked={enabled} />
            {/* TODO: add filter prop to only show unmapped components */}
            <ComponentSelection name="component" value={componentKey} onChange={onChange} />
            <TextInput name="alias" value={alias} onChange={onChange} />
        </TableRow>
    );
};

ProcessVariable.propTypes = {
    index: PropTypes.number.isRequired,
    enabled: PropTypes.bool,
    componentKey: PropTypes.string,
    alias: PropTypes.string,
};


const SelectProcessVariables = ({ onChange }) => {
    return (
        <ChangelistTableWrapper headColumns={<HeadColumns />}>

            <ProcessVariable index={0} enabled />
            <ProcessVariable index={1} enabled={false} />
            <ProcessVariable index={2} enabled />

        </ChangelistTableWrapper>
    );
};

SelectProcessVariables.propTypes = {
    onChange: PropTypes.func.isRequired,
};


export default SelectProcessVariables;
