const COMPONENT_DATATYPES = {
    'date': 'datetime',
    'time': 'time',
    'file': 'object',
    'currency': 'float',
    'number': 'float',
    'checkbox': 'boolean',
    'selectboxes': 'object',
    'npFamilyMembers': 'object',
    'map': 'array'
};


const DEFAULT_STATIC_VARIABLES = [
    {
        name: 'Now',
        key: 'now',
        source: 'component',
        dataType: 'datetime',
        initial_value: 'now',
    },
];

export {COMPONENT_DATATYPES, DEFAULT_STATIC_VARIABLES};
