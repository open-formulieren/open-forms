import React from 'react';
import PropTypes from 'prop-types';

import Types, {jsonComplex as COMPLEX_TYPES} from '../types';
import ArrayVariable from './ArrayVariable';
import ObjectVariable from './ObjectVariable';


const TYPE_MAP = {
    array: ArrayVariable,
    object: ObjectVariable,
};


const ComplexVariable = ({ type, definition=null, onChange, onEditDefinition }) => {
    const Component = TYPE_MAP[type];
    if (!Component) {
        throw new Error(`Component type '${type}' is not supported`);
    }
    return (
        <Component definition={definition} onChange={onChange} onEditDefinition={onEditDefinition} />
    );
};

ComplexVariable.propTypes = {
    type: PropTypes.oneOf(COMPLEX_TYPES).isRequired,
    definition: PropTypes.oneOfType([
        PropTypes.arrayOf(Types.VariableDefinition),
        PropTypes.objectOf(Types.VariableDefinition),
    ]),
    onChange: PropTypes.func.isRequired,
    onEditDefinition: PropTypes.func.isRequired,
};

export default ComplexVariable;
