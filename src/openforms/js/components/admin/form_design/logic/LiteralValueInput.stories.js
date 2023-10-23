import {FormDecorator} from '../story-decorators';
import LiteralValueInput from './LiteralValueInput';

export default {
  title: 'Form design / LiteralValueInput',
  component: LiteralValueInput,
  decorators: [FormDecorator],
  args: {
    name: 'aValue',
    type: 'string',
    value: undefined,
  },
};

export const Text = {
  name: 'String',
  args: {
    type: 'string',
  },
};

export const NumFloat = {
  name: 'Float',
  args: {
    type: 'float',
  },
};

export const NumInt = {
  name: 'Int',
  args: {
    type: 'int',
  },
};

export const DateTime = {
  args: {
    type: 'datetime',
  },
};

export const Date_ = {
  name: 'Date',
  args: {
    type: 'date',
  },
};

export const Bool = {
  name: 'Boolean',
  args: {
    type: 'boolean',
  },
};

export const Arr = {
  name: 'Array',
  args: {
    type: 'array',
  },
};

export const ArrWithValues = {
  name: 'Array with values',
  args: {
    type: 'array',
    value: ['Item 1', 'Item 2'],
  },
};

export const Obj = {
  name: 'Object',
  args: {
    type: 'object',
  },
};
