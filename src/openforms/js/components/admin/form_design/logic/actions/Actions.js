import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import ComponentSelection from '../../../forms/ComponentSelection';
import Select from '../../../forms/Select';
import {MODIFIABLE_PROPERTIES, STRING_TO_TYPE, TYPE_TO_STRING} from '../constants';
import OperandTypeSelection from '../OperandTypeSelection';
import LiteralValueInput from '../LiteralValueInput';
import {ComponentsContext} from '../../../forms/Context';
import StepSelection from '../StepSelection';
import {Action as ActionType} from './types';


const ActionProperty = ({action, errors, onChange}) => {
    const modifiablePropertyChoices = Object.entries(MODIFIABLE_PROPERTIES).map(
        ([key, info]) => [key, info.label]
    );

    const castValueTypeToString = (action) => {
        const valueType = action.action.property.type;
        const value = action.action.state;
        return (
            value
            ? TYPE_TO_STRING[valueType](value)
            : value
        );
    };

    const castValueStringToType = (value) => {
        const valueType = action.action.property.type;
        return STRING_TO_TYPE[valueType](value);
    };

    return (
        <>
            <div className="dsl-editor__node">
                <ComponentSelection
                    name="component"
                    value={action.component}
                    onChange={onChange}
                />
            </div>
            <div className="dsl-editor__node">
                <Select
                    name="action.property"
                    choices={modifiablePropertyChoices}
                    translateChoices
                    allowBlank
                    onChange={(e) => {
                        const propertySelected = e.target.value;
                        const fakeEvent = {
                            target: {
                                name: e.target.name,
                                value: {
                                    type: MODIFIABLE_PROPERTIES[propertySelected]?.type || '',
                                    value: propertySelected,
                                }
                            }
                        }
                        onChange(fakeEvent);
                    }}
                    value={action.action.property.value}
                />
            </div>
            {
                MODIFIABLE_PROPERTIES[action.action.property.value] &&
                <div className="dsl-editor__node">
                    <Select
                        name="action.state"
                        choices={MODIFIABLE_PROPERTIES[action.action.property.value].options}
                        translateChoices
                        allowBlank
                        onChange={(event) => {
                            onChange({
                                target: {
                                    name: event.target.name,
                                    value: castValueStringToType(event.target.value)
                                }
                            })
                        }}
                        value={castValueTypeToString(action)}
                    />
                </div>
            }
        </>
    );
};

const ActionValue = ({action, errors, onChange}) => {
    const allComponents = useContext(ComponentsContext);
    const componentType = allComponents[action.component]?.type;

    const getValueSource = (action) => {
        if (!action.component) return '';

        return (
           action.action.value.hasOwnProperty('var') ? 'component' : 'literal'
        );
    };

    const valueSource = getValueSource(action);
    return (
        <>
            <div className="dsl-editor__node">
                <ComponentSelection
                    name="component"
                    value={action.component}
                    onChange={onChange}
                />
            </div>
            <div className="dsl-editor__node">
                <OperandTypeSelection
                    name="action.value"
                    onChange={(e) => {
                        onChange({
                            target: {
                                name: e.target.name,
                                value: e.target.value === 'component' ? {var: ''} : ''
                            }
                        });
                    }}
                    operandType={valueSource}
                    filter={
                        ([choiceKey, choiceLabel]) => ['literal', 'component'].includes(choiceKey)
                    }
                />
            </div>
            {
                valueSource === 'literal' &&
                <div className="dsl-editor__node">
                    <LiteralValueInput
                        name="action.value"
                        componentType={componentType}
                        value={action.action.value}
                        onChange={onChange}
                    />
                </div>
            }
            {
                valueSource === 'component' &&
                <div className="dsl-editor__node">
                    <ComponentSelection
                        name="action.value.var"
                        value={action.action.value.var}
                        onChange={onChange}
                        filter={(comp) => (comp.type === componentType)}
                    />
                </div>
            }
        </>
    );
};

const ActionStepNotApplicable = ({action, errors, onChange}) => {
    return (
        <div className="dsl-editor__node">
            <StepSelection
                name="formStep"
                value={action.formStep}
                onChange={onChange}
            />
        </div>
    );
};


const ActionComponent = ({action, errors, onChange}) => {
    let Component;
    switch (action.action.type) {
        case 'property': {
           Component = ActionProperty;
           break;
        }
        case 'value': {
            Component = ActionValue;
            break;
        }
        case '':
        case 'disable-next':{
            return null;
        }
        case 'step-not-applicable':{
            Component = ActionStepNotApplicable;
            break;
        }
        default: {
            throw new Error(`Unknown action type: ${action.action.type}`);
        }
    }

    return (<Component action={action} errors={errors} onChange={onChange}/>);
};

ActionComponent.propTypes = {
    action: ActionType.isRequired,
    errors: PropTypes.array,
    onChange: PropTypes.func.isRequired,
};


export {ActionComponent};
