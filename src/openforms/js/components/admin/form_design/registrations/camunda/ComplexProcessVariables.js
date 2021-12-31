import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';
import {useImmerReducer} from 'use-immer';

import FormModal from '../../../FormModal';
import ButtonContainer from '../../../forms/ButtonContainer';
import {Checkbox} from '../../../forms/Inputs';
import {ChangelistTableWrapper, HeadColumn, TableRow} from '../../../tables';
import DeleteIcon from '../../../DeleteIcon';
import {jsonComplex as COMPLEX_JSON_TYPES} from '../../../json_editor/types';


const HeadColumns = () => {
    const intl = useIntl();

    const enabledText = (<FormattedMessage
        description="Manage complex process vars enabled checkbox column title"
        defaultMessage="Enabled"
    />);
    const enabledHelp = intl.formatMessage({
        description: 'Manage complex process vars enabled checkbox help text',
        defaultMessage: 'Check to include the field as process variable',
    });

    const aliasText = (<FormattedMessage
        description="Manage complex process vars alias column title"
        defaultMessage="Name"
    />);
    const aliasHelp = intl.formatMessage({
        description: 'Manage process vars alias help text',
        defaultMessage: 'The variable name to be used for the process instance.',
    });

    const editText = (<FormattedMessage
        description="Manage complex process vars configure column title"
        defaultMessage="Configure"
    />);

    return (
        <>
            <HeadColumn content={enabledText} title={enabledHelp} />
            <HeadColumn content={aliasText} title={aliasHelp} />
            <HeadColumn content={editText} />
        </>
    );
};


const ProcessVariable = ({ index, enabled=true, alias='', onChange, onDelete, onConfigure }) => {
    const intl = useIntl();

    const onCheckboxChange = (event, current) => {
        const { target: {name} } = event;
        onChange({target: {name, value: !current}});
    };

    const confirmDeleteMessage = intl.formatMessage({
        description: 'Camunda process variable mapping delete confirmation message',
        defaultMessage: 'Are you sure you want to remove this variable?',
    });

    return (
        <TableRow index={index}>
            <div className="actions actions--horizontal actions--roomy">
                <DeleteIcon onConfirm={onDelete} message={confirmDeleteMessage} />
                <Checkbox
                    name="enabled"
                    label=""
                    checked={enabled}
                    onChange={event => onCheckboxChange(event, enabled)}
                />
            </div>

            <span>{alias}</span>

            <a href="#" onClick={onConfigure}>
                <FormattedMessage
                    description="Manage complex process vars configure link text"
                    defaultMessage="Configure"
                />
            </a>
        </TableRow>
    );
};

ProcessVariable.propTypes = {
    index: PropTypes.number.isRequired,
    enabled: PropTypes.bool,
    alias: PropTypes.string,
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onConfigure: PropTypes.func.isRequired,
};


const initialState = {
    modalOpen: false,
    editVariableIndex: null,
};

const reducer = (draft, action) => {
    switch (action.type) {
        case 'CONFIGURE_VARIABLE': {
            const index = action.payload;
            draft.modalOpen = true;
            draft.editVariableIndex = index;
            break;
        }
        case 'RESET': {
            return initialState;
        }
        default: {
            throw new Error(`Unknown action type '${action.type}'`);
        }
    }
};

const ComplexProcessVariables = ({ variables=[], onChange, onAdd, onDelete }) => {

    const [
        {modalOpen, editVariableIndex},
        dispatch,
    ] = useImmerReducer(reducer, initialState);

    const editVariable = variables[editVariableIndex];

    return (
        <>
            <ChangelistTableWrapper headColumns={<HeadColumns />} extraModifiers={['camunda-vars']}>
                {
                    variables.map((processVar, index) => (
                        <ProcessVariable
                            key={index}
                            index={index}
                            onChange={onChange.bind(null, index)}
                            onDelete={onDelete.bind(null, index)}
                            onConfigure={(event) => {
                                event.preventDefault();
                                dispatch({type: 'CONFIGURE_VARIABLE', payload: index})
                            }}
                            {...processVar}
                        />
                    ))
                }
            </ChangelistTableWrapper>

            <ButtonContainer onClick={onAdd}>
                <FormattedMessage description="Add process variable button" defaultMessage="Add variable" />
            </ButtonContainer>

            <FormModal
                isOpen={modalOpen}
                closeModal={() => dispatch({type: 'RESET'}) }
                title={<FormattedMessage
                    description="Camunda complex process var configuration modal title"
                    defaultMessage="Edit complex variable"
                />}
            >
                {
                    editVariable
                    ? (
                        <code>
                            <pre>{JSON.stringify(editVariable, null, 4)}</pre>
                        </code>
                    )
                    : null
                }
            </FormModal>
        </>
    );
};

ComplexProcessVariables.propTypes = {
    variables: PropTypes.array,
    onChange: PropTypes.func.isRequired,
    onAdd: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};


export default ComplexProcessVariables;
