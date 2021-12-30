import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Fieldset from '../../forms/Fieldset';
import ComplexVariable from '../complex_variables';
import Types, {jsonComplex as COMPLEX_TYPES} from '../types';


const ComplexManualVariable = ({ name, type, definition=null, parent=null, onEditDefinition, onChange }) => {
    if (!COMPLEX_TYPES.includes(type)) return null;

    const onComplexVariableChange = (newDefinition) => {
        const fakeEvent = {
            target: {
                name: 'definition',  // TODO: lift up in parent component?
                value: newDefinition,
            },
        };
        onChange(fakeEvent);
    };

    // keep track of the parent(s)
    const self = {
        name: name,
        definition: {
            source: 'manual',
            type,
            definition
        },
        parent,
    };

    const onComplexVariableEditDefinition = ({ name, definition }) => {
        onEditDefinition({name, definition, parent: self});
    };

    return (
        <Fieldset title={<FormattedMessage
            description="JSON editor: complex variable definition title"
            defaultMessage="Variable definition"
        />}>
            <ComplexVariable
                type={type}
                definition={definition}
                onChange={onComplexVariableChange}
                onEditDefinition={onComplexVariableEditDefinition}
            />
        </Fieldset>
    );
};

ComplexManualVariable.propTypes = {
    name: Types.VariableIdentifier.isRequired,
    type: Types.VariableType.isRequired,
    definition: PropTypes.oneOfType([
        Types.VariableDefinition,
        Types.LeafVariableDefinition,
    ]),
    parent: Types.VariableParent,
    onEditDefinition: PropTypes.func.isRequired,
    onChange: PropTypes.func.isRequired,
};


export default ComplexManualVariable;
