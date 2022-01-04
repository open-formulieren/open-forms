import isEqual from 'lodash/isEqual';
import React, {useState, useEffect} from 'react';
import PropTypes from 'prop-types';
import {produce} from 'immer';
import {FormattedMessage} from 'react-intl';

import ButtonContainer from '../../forms/ButtonContainer';
import {TextInput} from '../../forms/Inputs';
import TypeRepresentation from '../TypeRepresentation';
import Types from '../types';
import ValueRepresentation from '../ValueRepresentation';


const ObjectKeyValuePair = ({ name='', definition={}, onNameChange, onEditDefinition }) => {

    const onEditClick = (event) => {
        event.preventDefault();
        onEditDefinition({name, definition});
    }

    return (
        <div style={{
            display: 'flex',
            justifyContent: 'flex-start',
            alignItems: 'center',
            padding: '5px',
        }}>
            <div style={{width: '100%', paddingRight: '5px'}}>
                <TextInput name="name" value={name} onChange={onNameChange} style={{width: '100%'}} />
            </div>

            <div style={{width: '100%', paddingRight: '5px'}}>
                <TypeRepresentation definition={definition} />
            </div>

            <div style={{
                width: '100%',
                paddingLeft: '5px',
                display: 'flex',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
            }}>

                <div>
                    <ValueRepresentation definition={definition} />
                </div>

                <div>
                {
                    !name
                    ? (<FormattedMessage
                        description="JSON editor: object entry has empty key name"
                        defaultMessage="Set a key name before you can configure this variable" />)
                    : (
                        <a href="#" onClick={onEditClick}>
                            <FormattedMessage
                                description="JSON editor: edit value definition"
                                defaultMessage="Edit definition"
                            />
                        </a>
                    )
                }
                </div>
            </div>
        </div>
    );
};


ObjectKeyValuePair.propTypes = {
    name: PropTypes.string.isRequired,
    definition: Types.VariableDefinition,
    onNameChange: PropTypes.func.isRequired,
    onEditDefinition: PropTypes.func.isRequired,
};


const ObjectVariable = ({ definition=null, onChange, onEditDefinition }) => {
    // normalize to object
    definition = definition || {};

    // keep the ordering consistent when replacing keys so that the UI doesn't jump
    // around. For that, we convert the object into an array of objects with
    // deterministic ordering.
    const [pairs, setPairs] = useState([]);

    // synchronization step to track order in local state while keeping data-structure
    // clean in parent component
    useEffect(() => {
        const entries = Object.entries(definition);
        // compare the entries and the pairs. If they are not equal, we update the
        // pairs, as the definition prop is authorative.
        if (!isEqual(pairs, entries)) {
            const pairsStillPresent = pairs.filter(([key]) => key in definition);
            const keysStillPresent = pairsStillPresent.map(([key]) => key);
            const newPairs = entries.filter(([key]) => !keysStillPresent.includes(key))

            const allPairs = pairsStillPresent.concat(newPairs)
                .map(([key]) => [key, definition[key]]);
            setPairs(allPairs);
        }
    }, [definition]);

    const onAdd = (event) => {
        event.preventDefault();
        const randomName = Math.random().toString(16).substr(2, 8);
        const newPairs = produce(pairs, draft => {
            // add empty definition for randomly generated name
            draft.push([randomName, null]);
        });
        onChange(Object.fromEntries(newPairs));
    };

    const onKeyChange = (index, event) => {
        const {value: newName} = event.target;
        const newPairs = produce(pairs, draft => {
            draft[index][0] = newName;
        });
        setPairs(newPairs);
        onChange(Object.fromEntries(newPairs));
    };

    return (
        <div style={{padding: '10px'}}>
            <div style={{
                display: 'flex',
                justifyContent: 'flex-start',
                alignItems: 'center',
                padding: '5px',
            }}>
                <div style={{width: '100%', paddingRight: '5px'}}>
                    <strong>Key</strong>
                </div>
                <div style={{width: '100%', paddingRight: '5px'}}>
                    <strong>Type</strong>
                </div>
                <div style={{width: '100%', paddingLeft: '5px'}}>
                    <strong>Value</strong>
                </div>
            </div>
            {
                pairs.map(([name, valueDefinition], index) => (
                    <ObjectKeyValuePair
                        key={index}
                        name={name}
                        definition={valueDefinition}
                        onNameChange={onKeyChange.bind(null, index)}
                        onEditDefinition={onEditDefinition}
                    />
                ))
            }
            <ButtonContainer onClick={onAdd}>
                <FormattedMessage
                    description="JSON editor: add object key-value pair button"
                    defaultMessage="Add key-value pair"
                />
            </ButtonContainer>
        </div>
    );
};

ObjectVariable.propTypes = {
    definition: PropTypes.objectOf(Types.VariableDefinition),
    onChange: PropTypes.func.isRequired,
    onEditDefinition: PropTypes.func.isRequired,
};

export default ObjectVariable;
