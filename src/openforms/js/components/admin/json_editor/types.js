import PropTypes from 'prop-types';

// JSON types

const jsonPrimitives = [
    'string',
    'number',
    'boolean',
    'null',
];

export const jsonComplex = [
    'object',
    'array',
];

// (React) proptypes

export const VariableIdentifier = PropTypes.oneOfType([
    PropTypes.string,  // key in an object
    PropTypes.number,  // index in an array
]);

/*
Meta-information about the JSON type of a variable.
 */
export const VariableType = PropTypes.oneOf(
    [''] // empty/unset
    .concat(jsonPrimitives)
    .concat(jsonComplex)
);

/*
The definition of a variable. Type depends on the specified variable type and is
therefore polymorphic. Note that `null` is included by not using `.isRequired`.

These are essentially the JSON types mapped to proptypes.
 */
export const LeafVariableDefinition = PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
    PropTypes.bool,
    PropTypes.object,
    PropTypes.array,
]);


export const VariableSource = PropTypes.oneOf([
    '',
    'manual',
    'component',
    'interpolate',
]);


export const VariableDefinition = PropTypes.shape({
    source: VariableSource,
    definition: PropTypes.oneOfType([
        LeafVariableDefinition,
        PropTypes.object, // TODO: recursive `VariableDefinition` prop type
    ]), // can initially be null, so no `.isRequired`
    // optional, set if source is 'manual'
    // TODO: custom prop type to enforce this?
    type: VariableType,
});


/*
A variable may have a parent, which itself is described in Javascript objects.
 */
export const VariableParent = PropTypes.shape({
    name: PropTypes.oneOfType([
        PropTypes.string, // key in an object
        PropTypes.number, // index in an array
    ]).isRequired,
    definition: VariableDefinition,
    parent: PropTypes.object, // TODO: recursive `VariableParent` prop type
});


const Types = {
    VariableIdentifier,
    LeafVariableDefinition,
    VariableSource,
    VariableDefinition,
    VariableType,
    VariableParent,
};


export default Types;
