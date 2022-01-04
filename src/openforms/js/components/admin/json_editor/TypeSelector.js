import React from 'react';
import PropTypes from 'prop-types';

import Select from '../forms/Select';
import {TYPE_MESSAGES} from './TypeRepresentation';


export const TYPE_CHOICES = [
    {
        complex: true,
        value: 'array',
        label: TYPE_MESSAGES.array,
    },
    {
        complex: true,
        value: 'object',
        label: TYPE_MESSAGES.object,
    },
    {
        complex: false,
        value: 'string',
        label: TYPE_MESSAGES.string,
    },
    {
        complex: false,
        value: 'number',
        label: TYPE_MESSAGES.number,
    },
    {
        complex: false,
        value: 'boolean',
        label: TYPE_MESSAGES.boolean,
    },
    {
        complex: false,
        value: 'null',
        label: TYPE_MESSAGES.null,
    },
];


/**
 * Select a JSON datatype.
 *
 * Thin wrapper around a Select dropdown providing the available type choices.
 *
 * @param  {Boolean}   props.complexOnly   Whether to only display/allow complex
 *                                         datatypes. If true, primitives are not available.
 * @param  {...object} props.extra         Any extra props are forwarded to the underlying
 *                                         Select component.
 * @return {JSX}                           A Select dropdown with pre-defined choices.
 */
const TypeSelector = ({ complexOnly=false, ...extra }) => {
    const choices = TYPE_CHOICES
        .filter(opt => !complexOnly || (complexOnly && opt.complex))
        .map(opt => [opt.value, opt.label])
    ;
    return (
        <Select choices={choices} translateChoices allowBlank={false} {...extra} />
    );
};

TypeSelector.propTypes = {
    complexOnly: PropTypes.bool,
};


export default TypeSelector;
