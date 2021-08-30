import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';
import jsonLogic from 'json-logic-js';

import {OPERATORS} from './constants';
import Select from '../../forms/Select';
import {NumberInput} from '../../forms/Inputs';
import {getTranslatedChoices} from '../../../../utils/i18n';


const EMTPTY_RELATIVE_DELTA = [0, 0, 0];


const Today = ({name, value, onChange}) => {
    const sign = value ? jsonLogic.get_operator(value) : '+';
    var rdelta = value && value[sign][1]?.rdelta ? value[sign][1].rdelta : EMTPTY_RELATIVE_DELTA;
    if (rdelta.length < 3) {
        rdelta = [...rdelta].concat(EMTPTY_RELATIVE_DELTA).slice(0, 3);
    }

    const intl = useIntl();
    const operatorChoices = Object.entries(OPERATORS).filter(([operator]) => ['+', '-'].includes(operator));

    const onChangeSign = (event) => {
        const modifiedValue = {};
        modifiedValue[event.target.value] = [{today: []}, {rdelta: rdelta}];
        const fakeEvent = {target: {name: name, value: modifiedValue}};
        onChange(fakeEvent);
    };

    const onChangeRelativeDelta = (event) => {
        const modifiedValue = {};
        modifiedValue[sign] = [{today: []}, {rdelta: event.target.value}];
        const fakeEvent = {target: {name: name, value: modifiedValue}};
        onChange(fakeEvent);
    };

    return (
        <>
            <div className="dsl-editor__node">
                <Select
                    name="sign"
                    choices={getTranslatedChoices(intl, operatorChoices)}
                    onChange={onChangeSign}
                    value={sign}
                />
            </div>
            <div className="dsl-editor__node-group">
                <div className="dsl-editor__node">
                    <NumberInput
                        name="years"
                        value={rdelta[0]}
                        onChange={(event) => {
                            const fakeEvent = {
                                target: {
                                    value: [
                                        parseInt(event.target.value, 10),
                                        ...rdelta.slice(1, 3)
                                    ]
                                }
                            };
                            onChangeRelativeDelta(fakeEvent);
                        }}
                        min={0}
                    />
                </div>
                <div className="dsl-editor__node">
                    <FormattedMessage description="Logic trigger number of years" defaultMessage="years" />
                </div>
            </div>
            <div className="dsl-editor__node-group">
                <div className="dsl-editor__node">
                    <NumberInput
                        name="months"
                        value={rdelta[1]}
                        onChange={(event) => {
                            const fakeEvent = {
                                target: {
                                    value: [
                                        rdelta[0],
                                        parseInt(event.target.value, 10),
                                        rdelta[2]
                                    ]
                                }
                            };
                            onChangeRelativeDelta(fakeEvent);
                        }}
                        min={0}
                    />
                </div>
                <div className="dsl-editor__node">
                    <FormattedMessage description="Logic trigger number of months" defaultMessage="months" />
                </div>
            </div>
            <div className="dsl-editor__node-group">
                <div className="dsl-editor__node">
                    <NumberInput
                        name="days"
                        value={rdelta[2]}
                        onChange={(event) => {
                            const fakeEvent = {
                                target: {
                                    value: [
                                        ...rdelta.slice(0, 2),
                                        parseInt(event.target.value, 10)
                                    ]
                                }
                            };
                            onChangeRelativeDelta(fakeEvent);
                        }}
                        min={0}
                    />
                </div>
                <div className="dsl-editor__node">
                    <FormattedMessage description="Logic trigger number of days" defaultMessage="days" />
                </div>
            </div>
        </>
    );
};

Today.propTypes = {
    name: PropTypes.string.isRequired,
    value: PropTypes.object.isRequired,
    onChange: PropTypes.func.isRequired,
};

export default Today;
