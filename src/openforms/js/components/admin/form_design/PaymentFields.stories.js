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
        id: 'ogone-legacy',
        label: 'Ogone legacy',
        schema: {
          type: 'object',
          properties: {
            merchantId: {
              type: 'integer',
              enum: [1, 2],
              enumNames: ['Merchant 1', 'Merchant 2'],
              title: 'Merchant id',
              description: 'Merchant to use',
            },
          },
          required: ['merchantId'],
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

export const OgoneLegacy = {
  name: 'Ogone (legacy)',
  args: {
    selectedBackend: 'ogone-legacy',
    backendOptions: {
      merchantId: 2,
    },
  },
};
