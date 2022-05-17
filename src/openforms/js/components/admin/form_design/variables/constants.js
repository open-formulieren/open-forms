const COMPONENT_DATATYPES = {
    'textfield': 'string',
    'email': 'string',
    'date': 'datetime',
    'time': 'time',
    'phoneNumber': 'string',
};

// Component types that don't need to have an associated FormVariable
const NO_VARIABLE_COMPONENT = ['content', 'fieldset', 'column'];

const DEFAULT_STATIC_VARIABLES = [
    {
        name: 'Now',
        key: 'now',
        source: 'component',
        dataType: 'datetime',
        initial_value: 'now',
    },
];

export {COMPONENT_DATATYPES, NO_VARIABLE_COMPONENT, DEFAULT_STATIC_VARIABLES};
