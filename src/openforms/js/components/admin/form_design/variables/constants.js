import React from 'react';
import {FormattedMessage, defineMessage} from 'react-intl';

const COMPONENT_DATATYPES = {
  date: 'date',
  time: 'time',
  file: 'array',
  currency: 'float',
  number: 'float',
  checkbox: 'boolean',
  selectboxes: 'object',
  npFamilyMembers: 'object',
  map: 'array',
  editgrid: 'array',
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
    'date',
    defineMessage({
      description: 'data type date',
      defaultMessage: 'Date',
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

const VARIABLE_SOURCES = {
  component: 'component',
  userDefined: 'user_defined',
};

const VARIABLE_SOURCES_GROUP_LABELS = {
  userDefined: 'user variables',
  component: 'component variables',
  static: 'static variables',
};

const EMPTY_VARIABLE = {
  name: '',
  key: '',
  formDefinition: '',
  source: VARIABLE_SOURCES.userDefined,
  prefillPlugin: '',
  prefillAttribute: '',
  prefillIdentifierRole: 'main',
  isSensitiveData: false,
  dataType: 'string',
  initial_value: '',
  serviceFetchConfiguration: null,
};

const IDENTIFIER_ROLE_CHOICES = {
  main: defineMessage({
    description: 'Identifier role (for mandate context) label for representee',
    defaultMessage: 'Main/representee',
  }),
  authorizee: defineMessage({
    description: 'Identifier role (for mandate context) label for authorizee',
    defaultMessage: 'Authorizee',
  }),
};

export {
  COMPONENT_DATATYPES,
  VARIABLE_SOURCES,
  VARIABLE_SOURCES_GROUP_LABELS,
  DATATYPES_CHOICES,
  EMPTY_VARIABLE,
  IDENTIFIER_ROLE_CHOICES,
};
