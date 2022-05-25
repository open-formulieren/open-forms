import {defineMessage} from 'react-intl';

const COMPONENT_DATATYPES = {
  date: 'datetime',
  time: 'time',
  file: 'object',
  currency: 'float',
  number: 'float',
  checkbox: 'boolean',
  selectboxes: 'object',
  npFamilyMembers: 'object',
  map: 'array',
};

const DATATYPES_CHOICES = [
  [
    'string',
    defineMessage({
      description: 'data type string',
      defaultMessage: 'String',
    }),
  ],
  [
    'boolean',
    defineMessage({
      description: 'data type boolean',
      defaultMessage: 'Boolean',
    }),
  ],
  [
    'object',
    defineMessage({
      description: 'data type object',
      defaultMessage: 'Object',
    }),
  ],
  [
    'array',
    defineMessage({
      description: 'data type array',
      defaultMessage: 'Array',
    }),
  ],
  [
    'int',
    defineMessage({
      description: 'data type int',
      defaultMessage: 'Integer',
    }),
  ],
  [
    'float',
    defineMessage({
      description: 'data type float',
      defaultMessage: 'Float',
    }),
  ],
  [
    'datetime',
    defineMessage({
      description: 'data type datetime',
      defaultMessage: 'Datetime',
    }),
  ],
  [
    'time',
    defineMessage({
      description: 'data type time',
      defaultMessage: 'Time',
    }),
  ],
];

const DEFAULT_STATIC_VARIABLES = [
  {
    name: 'Now',
    key: 'now',
    source: 'component',
    dataType: 'datetime',
    initial_value: 'now',
  },
];

const VARIABLE_SOURCES = {
  static: 'static',
  component: 'component',
  userDefined: 'user_defined',
};

const EMPTY_VARIABLE = {
  name: '',
  key: '',
  formDefinition: '',
  source: VARIABLE_SOURCES.userDefined,
  prefillPlugin: '',
  prefillAttribute: '',
  isSensitiveData: false,
  dataType: 'string',
  initial_value: '',
};

export {
  COMPONENT_DATATYPES,
  DEFAULT_STATIC_VARIABLES,
  VARIABLE_SOURCES,
  DATATYPES_CHOICES,
  EMPTY_VARIABLE,
};
