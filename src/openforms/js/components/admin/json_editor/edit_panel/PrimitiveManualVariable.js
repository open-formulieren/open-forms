import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../../forms/Field';
import FormRow from '../../forms/FormRow';
import {TextInput, NumberInput} from '../../forms/Inputs';
import Select from '../../forms/Select';
import Types from '../types';
import TypeSelector from '../TypeSelector';


const PrimitiveManualVariable = ({ type='', definition=null, onChange }) => {

    let variableInput = null;

    switch (type) {
        case 'string': {
            variableInput = (
                <TextInput name="value" value={definition || ''} onChange={onChange} />
            );
            break;
        }
        case 'number': {
            variableInput = (
                <NumberInput name="value" value={definition || ''} onChange={onChange} />
            );
            break;
        }
        case 'boolean': {
            variableInput = (
                <Select
                    choices={[['true', 'true'], ['false', 'false']]}
                    allowBlank
                    value={(definition == null || definition === '') ? '' : definition ? 'true' : 'false'}
                    onChange={onChange}
                />
            );
            break;
        }
    }

    return (
        <>
            <FormRow>
                <Field name="type" label={<FormattedMessage
                    description="JSON datatype selector label"
                    defaultMessage="Type"
                />}>
                    <TypeSelector value={type} onChange={onChange} allowBlank />
                </Field>
            </FormRow>
            {
                variableInput
                ? (
                    <FormRow>
                        <Field name="definition" label={<FormattedMessage
                            description="JSON (primitive) value label"
                            defaultMessage="Value"
                        />}>
                            {variableInput}
                        </Field>
                    </FormRow>
                )
                : null
            }
        </>
    );
};

PrimitiveManualVariable.propTypes = {
    type: Types.VariableType.isRequired,
    definition: Types.LeafVariableDefinition,
    onChange: PropTypes.func.isRequired,
};


export default PrimitiveManualVariable;
