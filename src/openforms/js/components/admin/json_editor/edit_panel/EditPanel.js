import React, {useEffect} from 'react';
import PropTypes from 'prop-types';
import {useImmerReducer} from 'use-immer';
import {FormattedMessage, useIntl} from 'react-intl';

import {SubmitAction} from '../../forms/ActionButton';
import SubmitRow from '../../forms/SubmitRow';
import Types from '../types';
import EditVariable from './EditVariable';


const initialState = {
    source: 'component',
    component: '',
    expression: {},
    manual: {
        type: '',
        definition: null,
    },
};


const reducer = (draft, action) => {
    switch (action.type) {
        case 'LOAD_EXISTING_DEFINITION': {
            const {source, type, definition} = action.payload;

            switch (source) {
                case 'component': {
                    // initially, simple jsonLogic support {"var": "componentKey"}
                    draft.component = definition?.var || '';
                    break;
                }
                case 'manual': {
                    draft.manual.type = type;
                    draft.manual.definition = definition;
                    break;
                }
                case 'interpolate': {
                    draft.expression = definition;
                    break;
                }
                default: {
                    throw new Error(`Unknown var source ${source}`);
                }
            }

            draft.source = source;
            break;
        }
        case 'FIELD_CHANGED': {
            const {name, value} = action.payload;
            draft[name] = value;
            break;
        }
        case 'MANUAL_VARIABLE_FIELD_CHANGED': {
            const {name, value} = action.payload;
            draft.manual[name] = value;

            // type change -> reset value
            if (name === 'type') {
                draft.manual.definition = null;
            }

            // handle type-conversion for boolean select
            if (name === 'value' && draft.manual.type === 'boolean') {
                let castValue = null;
                if (value === 'true') castValue = true;
                if (value === 'false') castValue = false;
                draft.manual.definition = castValue;
            }

            break;
        }
        case 'RESET': {
            return initialState;
        }
    }
};


const EditPanel = ({ name, definition=null, parent=null, onEditDefinition, onChange, onCancel }) => {
    const originalParent = parent;

    // hooks
    const intl = useIntl();
    const [
        {source, component, manual, expression},
        dispatch,
    ] = useImmerReducer(reducer, initialState)

    // consolidate local state and prop definition - we only save changes from
    // state to parent component after explicit button click, but we need to load
    // existing configuration into the state too
    useEffect(() => {
        // no pre-existing definition
        if (!definition) {
            dispatch({type: 'RESET'});
        } else {
            dispatch({
                type: 'LOAD_EXISTING_DEFINITION',
                payload: definition
            });
        }
        return () => dispatch({type: 'RESET'});
    }, [definition, originalParent]);

    // event handlers
    const onFieldChange = (event) => dispatch({
        type: 'FIELD_CHANGED',
        payload: event.target,
    });

    const onManualChange = (event) => dispatch({
        type: 'MANUAL_VARIABLE_FIELD_CHANGED',
        payload: event.target,
    });

    const onConfirm = (event) => {
        event.preventDefault();

        let variableDefinition = null;
        switch (source) {
            case 'component': {
                // most simple json logic expression initially, later this can become
                // more complex - see also the interpolate variant.
                variableDefinition = {
                    definition: {var: component}
                };
                break;
            }
            case 'manual': {
                variableDefinition = {
                    type: manual.type,
                    definition: manual.definition,
                };
                break;
            }
            case 'interpolate': {
                variableDefinition = {definition: expression};
                break;
            }
            // TODO: if none match, throw error/render validation errors
        }
        variableDefinition.source = source;
        dispatch({type: 'RESET'});
        onChange(variableDefinition, originalParent);
    };

    // manage the different sources of variables
    let dependentFieldsOnChange;

    switch(source) {
        case 'component': {
            dependentFieldsOnChange = onFieldChange;
            break;
        }
        case 'manual': {
            dependentFieldsOnChange = onManualChange;
            break;
        }
        case 'interpolate': {
            dependentFieldsOnChange = onFieldChange;
            break;
        }
    }

    const nameBits = [name];
    while (parent != null) {
        nameBits.push(parent.name);
        parent = parent.parent;
    }
    const jsonPathName = nameBits.reverse().join('.');

    // render the full component tree
    return (
        <>
            <header className="react-modal__header">
                <h2 className="react-modal__title">
                    <FormattedMessage
                        description="JSON editor: variable edit panel title"
                        defaultMessage="Edit variable {name}"
                        values={{name: jsonPathName}}
                    />
                </h2>
            </header>

            <div className="react-modal__form">

                <EditVariable
                    name={name}
                    source={source}
                    component={component}
                    manual={manual}
                    expression={expression}
                    parent={originalParent}
                    onFieldChange={onFieldChange}
                    onManualChange={onManualChange}
                    dependentFieldsOnChange={dependentFieldsOnChange}
                    onEditDefinition={onEditDefinition}
                />

                <SubmitRow>
                    <a href="#" onClick={(event) => {
                        event.preventDefault();
                        dispatch({type: 'RESET'});
                        onCancel();
                    }}>
                        <FormattedMessage
                            description="JSON editor: cancel variable edit"
                            defaultMessage="Cancel"
                        />
                    </a>
                    <SubmitAction text={intl.formatMessage({
                        description: 'JSON editor: confirm edited variable definition',
                        defaultMessage: 'Confirm',
                    })} onClick={onConfirm} />
                </SubmitRow>
            </div>
        </>
    );
};

EditPanel.propTypes = {
    name: Types.VariableIdentifier.isRequired,
    definition: Types.VariableDefinition,
    parent: Types.VariableParent,
    onEditDefinition: PropTypes.func.isRequired,
    onCancel: PropTypes.func.isRequired,
    onChange: PropTypes.func.isRequired,
};

export default EditPanel;
