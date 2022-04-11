import React from 'react';
import PropTypes from 'prop-types';
import {produce} from 'immer';
import {useImmerReducer} from 'use-immer';
import {FormattedMessage, useIntl} from 'react-intl';

import FormModal from '../../../FormModal';
import {SubmitAction} from '../../../forms/ActionButton';
import {TextInput} from '../../../forms/Inputs';
import Field from '../../../forms/Field';
import Fieldset from '../../../forms/Fieldset';
import FormRow from '../../../forms/FormRow';
import Select from '../../../forms/Select';
import SubmitRow from '../../../forms/SubmitRow';
import {ComplexVariable, EditPanel, TypeSelector} from '../../../json_editor';
import {jsonComplex as COMPLEX_JSON_TYPES} from '../../../json_editor/types';


const initialState = {
    // variable definition/state
    type: 'object',
    definition: {},
    // edit panel state
    editPanelOpen: false,
    editVariable: {
        name: '',
        definition: null,
        parent: null,
    },
};


const reducer = (draft, action) => {
    switch (action.type) {
        case 'FIELD_CHANGED': {
            const {name, value} = action.payload;
            draft[name] = value;
            if (name === 'type') {
                draft.definition = null;
            }
            break;
        }
        case 'START_EDIT_VARIABLE_DEFINITION': {
            const {name, definition, parent} = action.payload;
            draft.editPanelOpen = true;
            draft.editVariable = {
                name,
                definition,
                parent,
            };
            break;
        }
        case 'SAVE_VARIABLE_DEFINITION': {
            const {name, definition: newDefinition, parent} = action.payload;

            // two possible paths:
            // * parent is set, so we updated the definition of the parent and change
            //   the state of the edit panel
            // * parent is null, which means we're editing the root object, so we
            //   update the draft state and close the edit panel

            if (parent != null) {
                // update edit panel state
                // parent is originally from a prop, so it's immutable, which is why we
                // use the produce from immer inside of the immer reducer
                const parentDefinition = produce(parent.definition, definitionDraft => {
                    definitionDraft.definition[name] = newDefinition;
                });

                // let the editVariable state 'crawl' up a level
                draft.editVariable = {
                    name: parent.name,
                    definition: parentDefinition,
                    parent: parent.parent,
                }
                // do not fall down into edit panel reset, so that the panel stays open
                // and maintains its state
                break;
            } else {
                // update draft definition
                // name is either an object key or a list index, both work with the
                // same syntax and explicit casting is not needed.
                draft.definition[name] = newDefinition;
            }

            // fall through to reset edit panel so it gets closed and state is reset
        }
        case 'CANCEL_EDIT_VARIABLE_DEFINITION': {
            const {parent} = draft.editVariable;
            if (parent) {
                draft.editVariable = {
                    name: parent.name,
                    definition: parent.definition,
                    parent: parent.parent,
                };
                break;
            }
        }
        case 'RESET_EDIT_PANEL': {
            // reset edit state
            draft.editVariable = initialState.editVariable;
            // close the panel
            draft.editPanelOpen = false;
            break;
        }
        default: {
            throw new Error(`Unknown action type '${action.type}'`);
        }
    }
};


const editPanelStyle = {
    borderLeft: 'solid 1px #ddd',
    boxShadow: '-2px 0 3px rgba(0, 0, 0, 0.1)',
    padding: '20px',
    position: 'absolute',
    zIndex: '2',
    top: '0',
    bottom: '0',
    right: '0',
    left: '10%',
    background: 'var(--body-bg)',
    flexDirection: 'column',
};


const ComplexProcessVariable = ({
    name, type: initialType, definition: initialDefinition,
    onConfirm,
}) => {
    const intl = useIntl();

    // state
    const [
        {
            type, definition,
            editPanelOpen, editVariable,
        },
        dispatch
    ] = useImmerReducer(reducer, {
        ...initialState,
        type: initialType,
        definition: initialDefinition,
    });

    // event handlers
    const onChange = (event) => dispatch({type: 'FIELD_CHANGED', payload: event.target});

    const onEditDefinition = ({ name, definition, parent=null }) => {
        dispatch({
            type: 'START_EDIT_VARIABLE_DEFINITION',
            payload: {
                name,
                definition,
                parent,
            },
        });
    };

    const onConfirmDefinition = (event) => {
        event.preventDefault();
        onConfirm({name, type, definition});
    };

    return (
        /* container */
        <section style={{display: 'flex', flexDirection: 'column', flexGrow: '1'}}>

            {/* main body */}
            <div className="react-modal__form">
                <Fieldset>
                    <FormRow>
                        <Field name="name" label={<FormattedMessage
                            description="Camunda complex process var 'name' label"
                            defaultMessage="Name"
                        />}>
                            <div className="readonly">{name}</div>
                        </Field>
                    </FormRow>

                    <FormRow>
                        <Field name="type" label={<FormattedMessage
                            description="Camunda complex process var 'type' label"
                            defaultMessage="Type"
                        />}>
                            <TypeSelector value={type} onChange={onChange} complexOnly />
                        </Field>
                    </FormRow>
                </Fieldset>

                <Fieldset title={<FormattedMessage
                    description="Camunda complex variable definition title"
                    defaultMessage="Variable definition"
                />}>
                    {/* Root node of an arbitrarily deep tree. */}
                    <ComplexVariable
                        type={type}
                        definition={definition}
                        onChange={(newDefinition) => dispatch({
                            type: 'FIELD_CHANGED',
                            payload: {name: 'definition', value: newDefinition}
                        })}
                        onEditDefinition={onEditDefinition}
                    />
                </Fieldset>

                <SubmitRow>
                    <SubmitAction text={intl.formatMessage({
                        description: 'Confirm complex Camunda variable definition',
                        defaultMessage: 'Confirm',
                    })} onClick={onConfirmDefinition} />
                </SubmitRow>
            </div>

            {/* variable edit panel */}
            <aside style={{
                ...editPanelStyle,
                display: editPanelOpen ? 'flex' : 'none',
            }}>
                {editPanelOpen
                    ? (<EditPanel
                        name={editVariable.name}
                        definition={editVariable.definition}
                        parent={editVariable.parent}
                        onEditDefinition={onEditDefinition}
                        onCancel={() => dispatch({type: 'CANCEL_EDIT_VARIABLE_DEFINITION'})}
                        onChange={(definition, parent) => dispatch({
                            type: 'SAVE_VARIABLE_DEFINITION',
                            payload: {
                                name: editVariable.name,
                                definition,
                                parent,
                            },
                        })}
                    />)
                    : null
                }
            </aside>

        </section>
    );
};

ComplexProcessVariable.propTypes = {
    name: PropTypes.string.isRequired,
    type: PropTypes.oneOf(COMPLEX_JSON_TYPES).isRequired,
    definition: PropTypes.oneOfType([
        PropTypes.object,
        PropTypes.array,
    ]).isRequired,
    onConfirm: PropTypes.func.isRequired,
};


export default ComplexProcessVariable;
