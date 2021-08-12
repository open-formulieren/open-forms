// TODO: these are the built in json logic operators, but it's possible to define
// custom operators. See https://jsonlogic.com/operations.html
// We start with a minimal supported set based on the user stories (and common sense).
// The data structure is a mapping of the actual json logic operator as key and the
// human readable label as value.
const OPERATORS = {
    '==': 'is equal to',
    '!=': 'is not equal to',
    '>': 'is greater than',
    '>=': 'is greater than or equal to',
    '<': 'is less than',
    '<=': 'is less than or equal to',
    'in': 'in', // array or string (!)
};


// map the Formio component types to allowed operators. Strings cannot be compared
// against each other for >=,>,<,<= etc., so this includes a logical allow-list to only
// show relevant components.
const COMPONENT_TYPE_TO_OPERATORS = {
    number: [
        '==',
        '!=',
        '>',
        '>=',
        '<',
        '<=',
    ],
    textfield: [
        '==',
        '!=',
        'in',
    ],
    iban: [
        '==',
        '!=',
        'in',
    ],
};


export { OPERATORS, COMPONENT_TYPE_TO_OPERATORS };
