import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import jsonLogic from 'json-logic-js';

import {OPERATORS} from './constants';
import Select from '../../forms/Select';
import {NumberInput} from '../../forms/Inputs';


const Today = ({name, value, onChange}) => {
    const sign = value ? jsonLogic.get_operator(value) : '+';
    const years = value ? value[sign][1]['years'] : 0;

    const intl = useIntl();

    const operatorChoices = Object
        .entries(OPERATORS)
        .filter(([operator]) => ['+', '-'].includes(operator))
        .map( ([operator, msg]) => [operator, intl.formatMessage(msg)] )
    ;

    const onChangeSign = (event) => {
        const modifiedValue = {};
        modifiedValue[event.target.value] = [{today: []}, {years: years}];
        const fakeEvent = {target: {name: name, value: modifiedValue}};
        onChange(fakeEvent);
    };

    const onChangeYears = (event) => {
        const modifiedValue = {};
        modifiedValue[sign] = [{today: []}, {years: parseInt(event.target.value, 10)}];
        const fakeEvent = {target: {name: name, value: modifiedValue}};
        onChange(fakeEvent);
    };

    return (
        <div className="dsl-editor__node-group">
            <div className="dsl-editor__node">
                <Select
                    name="sign"
                    choices={operatorChoices}
                    onChange={onChangeSign}
                    value={sign}
                />
            </div>
            <div className="dsl-editor__node">
                <NumberInput
                    name="years"
                    value={years}
                    onChange={onChangeYears}
                    min={0}
                />
            </div>
            <div className="dsl-editor__node">
                <FormattedMessage description="Logic trigger number of years" defaultMessage="years" />
            </div>
        </div>
    );
};

export default Today;
