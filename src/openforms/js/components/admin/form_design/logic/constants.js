import {defineMessage} from 'react-intl';

// TODO: these are the built in json logic operators, but it's possible to define
// custom operators. See https://jsonlogic.com/operations.html
// We start with a minimal supported set based on the user stories (and common sense).
// The data structure is a mapping of the actual json logic operator as key and the
// human readable label as value.
const OPERATORS = {
  '==': defineMessage({
    description: '"==" operator description',
    defaultMessage: 'is equal to',
  }),
  '!=': defineMessage({
    description: '"!=" operator description',
    defaultMessage: 'is not equal to',
  }),
  '>': defineMessage({
    description: '">" operator description',
    defaultMessage: 'is greater than',
  }),
  '>=': defineMessage({
    description: '">=" operator description',
    defaultMessage: 'is greater than or equal to',
  }),
  '<': defineMessage({
    description: '"<" operator description',
    defaultMessage: 'is less than',
  }),
  '<=': defineMessage({
    description: '"<=" operator description',
    defaultMessage: 'is less than or equal to',
  }),
  in: defineMessage({
    description: '"in" operator description',
    defaultMessage: 'in',
  }), // array or string (!}
  '+': defineMessage({
    description: '"+" operator description',
    defaultMessage: 'plus',
  }),
  '-': defineMessage({
    description: '"-" operator description',
    defaultMessage: 'minus',
  }),
};

// map the Formio component types to allowed operators. Strings cannot be compared
// against each other for >=,>,<,<= etc., so this includes a logical allow-list to only
// show relevant components.
const TYPE_TO_OPERATORS = {
  float: ['==', '!=', '>', '>=', '<', '<='],
  string: ['==', '!=', 'in'],
  datetime: ['==', '!=', '>', '>=', '<', '<='],
  date: ['==', '!=', '>', '>=', '<', '<='],
  _default: ['==', '!='],
};

const ACTION_TYPES = [
  [
    'disable-next',
    defineMessage({
      description: 'action type "disable-next" label',
      defaultMessage: 'disable continuing to the next form step.',
    }),
  ],
  [
    'property',
    defineMessage({
      description: 'action type "property" label',
      defaultMessage: 'change a property of a component.',
    }),
  ],
  [
    'variable',
    defineMessage({
      description: 'action type "variable" label',
      defaultMessage: 'change the value of a variable/component',
    }),
  ],
  [
    'fetch-from-service',
    defineMessage({
      description: 'action type "fetch-from-service" label',
      defaultMessage: 'fetch the value for a variable from a service',
    }),
  ],
  [
    'step-not-applicable',
    defineMessage({
      description: 'action type "step-not-applicable" label',
      defaultMessage: 'Mark the form step as not-applicable',
    }),
  ],
  [
    'step-applicable',
    defineMessage({
      description: 'action type "step-applicable" label',
      defaultMessage: 'Mark the form step as applicable',
    }),
  ],
  [
    'set-registration-backend',
    defineMessage({
      description: 'action type "set-registration-backend" label',
      defaultMessage: 'Set the registration backend to use for the submission',
    }),
  ],
  [
    'evaluate-dmn',
    defineMessage({
      description: 'action type "evaluate-dmn" label',
      defaultMessage: 'Evaluate DMN',
    }),
  ],
  [
    'synchronize-variables',
    defineMessage({
      description: 'action type "synchronize variables" label',
      defaultMessage: 'Synchronize variables',
    }),
  ],
];

// Action types that once they are selected need further configurations.
// For example, picking which property of a component should be changed.
const ACTIONS_WITH_OPTIONS = ['property'];

const TYPE_TO_OPERAND_TYPE = {
  float: ['literal', 'variable'],
  string: ['literal', 'variable', 'array'],
  datetime: ['literal', 'variable'],
  date: ['literal', 'variable', 'today'],
  object: ['literal'],
  _default: ['literal'],
};

const STRING_TO_TYPE = {
  bool: stringValue => (stringValue === 'true' ? true : stringValue === 'false' ? false : null),
  json: stringValue => JSON.parse(stringValue),
};

const TYPE_TO_STRING = {
  bool: typedValue => String(typedValue),
  json: typedValue => JSON.stringify(typedValue),
};

const BOOL_OPTIONS = [
  [
    'true',
    defineMessage({
      description: 'Component property boolean value "true"',
      defaultMessage: 'Yes',
    }),
  ],
  [
    'false',
    defineMessage({
      description: 'Component property boolean value "false"',
      defaultMessage: 'No',
    }),
  ],
];

const MODIFIABLE_PROPERTIES = {
  ['validate.required']: {
    label: defineMessage({
      description: 'component property "required" label',
      defaultMessage: 'required',
    }),
    type: 'bool',
    options: BOOL_OPTIONS,
  },
  hidden: {
    label: defineMessage({
      description: 'component property "hidden" label',
      defaultMessage: 'hidden',
    }),
    type: 'bool',
    options: BOOL_OPTIONS,
  },
  disabled: {
    label: defineMessage({
      description: 'component property "disabled" label',
      defaultMessage: 'disabled',
    }),
    type: 'bool',
    options: BOOL_OPTIONS,
  },
};

export {
  OPERATORS,
  TYPE_TO_OPERATORS,
  ACTION_TYPES,
  ACTIONS_WITH_OPTIONS,
  MODIFIABLE_PROPERTIES,
  STRING_TO_TYPE,
  TYPE_TO_STRING,
  TYPE_TO_OPERAND_TYPE,
  BOOL_OPTIONS,
};
