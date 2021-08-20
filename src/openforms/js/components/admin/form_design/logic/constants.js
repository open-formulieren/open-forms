import {defineMessage} from 'react-intl';

// TODO: these are the built in json logic operators, but it's possible to define
// custom operators. See https://jsonlogic.com/operations.html
// We start with a minimal supported set based on the user stories (and common sense).
// The data structure is a mapping of the actual json logic operator as key and the
// human readable label as value.
const OPERATORS = {
    '==': defineMessage({'description': '== operator description', defaultMessage: 'is equal to'}),
    '!=': defineMessage({'description': '!= operator description', defaultMessage: 'is not equal to'}),
    '>': defineMessage({'description': '> operator description', defaultMessage: 'is greater than'}),
    '>=': defineMessage({'description': '>= operator description', defaultMessage: 'is greater than or equal to'}),
    '<': defineMessage({'description': '< operator description', defaultMessage: 'is less than'}),
    '<=': defineMessage({'description': '<= operator description', defaultMessage: 'is less than or equal to'}),
    'in': defineMessage({'description': 'in operator description', defaultMessage: 'in'}), // array or string (!}
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

const ACTION_TYPES = [
    ['disable-next', 'disable continuing to the next form step.'],
    ['property', 'change a property of a component.'],
    ['value', 'change the value of a component']
];


// Action types that once they are selected need further configurations.
// For example, picking which property of a component should be changed.
const ACTIONS_WITH_OPTIONS = [
    'property',
    'value'
];


const MODIFIABLE_PROPERTIES = [
    ['required', 'required'],
    ['hidden', 'hidden'],
    ['disabled', 'disabled']
];


const PROPERTY_VALUES = [
  ['true', 'Yes'],
  ['false', 'No']
];


export {
    OPERATORS,
    COMPONENT_TYPE_TO_OPERATORS,
    ACTION_TYPES,
    ACTIONS_WITH_OPTIONS,
    MODIFIABLE_PROPERTIES,
    PROPERTY_VALUES,
};
