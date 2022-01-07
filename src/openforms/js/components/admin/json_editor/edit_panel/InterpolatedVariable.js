// TODO: this could probably be built nicer using Draft.js, if we get time to
// look into that :-)
import React from 'react';
import PropTypes from 'prop-types';
import {produce} from 'immer';

import DeleteIcon from '../../DeleteIcon';
import ButtonContainer from '../../forms/ButtonContainer';
import ComponentSelection from '../../forms/ComponentSelection';
import Field from '../../forms/Field';
import {TextInput} from '../../forms/Inputs';
import Fieldset from '../../forms/Fieldset';
import FormRow from '../../forms/FormRow';
import Types from '../types';


const isString = (arg) => {
    return (typeof arg === 'string' || arg instanceof String);
};


export const displayInterpolateExpression = (expression, useJSX=false) => {
    const bits = expression.cat || [];
    const formattedBits = bits.map((bit, index) => {
        if (isString(bit)) return bit;

        // otherwise it's an object
        const {var: component} = bit;
        const stringRepr = `\$\{${component}\}`;
        if (!useJSX) return stringRepr;
        return (<code key={index}>{stringRepr}</code>);
    });
    return useJSX ? formattedBits : formattedBits.join('');
};


const PartWrapper = ({ onDelete, children }) => {
    return (
        <span style={{display: 'inline-flex', alignItems: 'center'}}>
            <DeleteIcon onConfirm={onDelete} />
            {children}
        </span>
    );
};


const InterpolationBuilder = ({parts=[], onChange}) => {

    const onStringChange = (index, event) => {
        const {value} = event.target;
        const newParts = produce(parts, draft => {
            draft[index] = value;
        });
        onChange(newParts);
    };

    const onComponentChange = (index, event) => {
        const {value} = event.target;
        const newParts = produce(parts, draft => {
            draft[index].var = value;
        });
        onChange(newParts);
    };

    const onAddPart = (type, event) => {
        event.preventDefault();

        let newPart;
        switch (type) {
            case 'string': {
                newPart = '';
                break;
            }
            case 'component': {
                newPart = {var: ''};
                break;
            }
        }
        onChange([...parts, newPart]);
    };

    const onDeletePart = (index) => {
        const {value} = event.target;
        const newParts = produce(parts, draft => {
            draft.splice(index, 1);
        });
        onChange(newParts);
    };

    return (
        <>
            <span style={{display: 'flex', flexWrap: 'wrap'}}>
            {
                parts.map((part, index) => (
                    isString(part)
                    ? (
                        <PartWrapper key={index} onDelete={onDeletePart.bind(null, index)}>
                            <textarea
                                name="string"
                                rows="1"
                                columns={part.length || 10}
                                value={part}
                                onChange={onStringChange.bind(null, index)}
                                style={{width: 'auto'}}
                            />
                        </PartWrapper>
                    )
                    : (
                        <PartWrapper key={index} onDelete={onDeletePart.bind(null, index)}>
                            <ComponentSelection
                                name="component"
                                value={part.var}
                                onChange={onComponentChange.bind(null, index)}
                            />
                        </PartWrapper>
                    )
                ))
            }
            </span>

            <div style={{display: 'flex', marginLeft: 'calc(160px - 1em)', width: '100%'}}>
                <ButtonContainer onClick={onAddPart.bind(null, 'string')}>
                    Add text part
                </ButtonContainer>
                <ButtonContainer onClick={onAddPart.bind(null, 'component')}>
                    Add form field
                </ButtonContainer>
            </div>

        </>
    );
};

InterpolationBuilder.propTypes = {
    parts: PropTypes.arrayOf(PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.shape({var: PropTypes.string}),
    ])),
    onChange: PropTypes.func.isRequired,
};



const InterpolatedVariable = ({ expression={}, onChange }) => {

    const onDefinitionChange = (newParts) => {
        const newDefinition = {cat: newParts};
        onChange({target: {name: 'expression', value: newDefinition}});
    };

    return (
        <>
            <FormRow>
                <Field name="expression" label="Text">
                    <InterpolationBuilder
                        parts={expression.cat || []}
                        onChange={onDefinitionChange}
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field name="_expression" label="Resulting string">
                    <textarea
                        cols="40" rows="5"
                        value={displayInterpolateExpression(expression)}
                        readOnly
                    />
                </Field>
            </FormRow>
        </>
    );
};

InterpolatedVariable.propTypes = {
    expression: PropTypes.shape({
        cat: PropTypes.arrayOf(PropTypes.oneOfType([
            PropTypes.string,
            PropTypes.shape({var: PropTypes.string}),
        ])),
    }),  // JSON logic expression, using the cat operator. {cat: ["foo ", {"var": "bar"}, " baz"]}
    onChange: PropTypes.func.isRequired,
};


export default InterpolatedVariable;
