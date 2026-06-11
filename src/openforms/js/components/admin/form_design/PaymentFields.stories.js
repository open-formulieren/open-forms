import {fn} from 'storybook/test';

import {
  FormDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';

import PaymentFields from './PaymentFields';

export default {
  title: 'Form design / Payments / PaymentFields',
  decorators: [ValidationErrorsDecorator, FormDecorator],
  component: PaymentFields,
  args: {
    backends: [
      {id: 'demo', label: 'Demo', schema: {type: 'object', properties: {}}},
      {
        id: 'worldline',
        label: 'Worldline',
        schema: {
          type: 'object',
          properties: {
            merchant: {
              type: 'integer',
              enum: [1, 2],
              enumNames: ['Merchant 1', 'Merchant 2'],
              title: 'Merchant id',
              description: 'Merchant to use',
            },
          },
          required: ['merchant'],
        },
      },
    ],
    selectedBackend: '',
    backendOptions: {},
    onChange: fn(),
  },
};

export const NothingSelected = {};

export const Demo = {
  args: {
    selectedBackend: 'demo',
  },
};

export const Worldline = {
  name: 'Worldline',
  args: {
    selectedBackend: 'worldine',
    backendOptions: {
      merchant: 2,
    },
  },
};
