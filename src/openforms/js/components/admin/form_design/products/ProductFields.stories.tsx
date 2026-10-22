import type {Meta, StoryObj} from '@storybook/react-vite';
import {expect, fn, userEvent, within} from 'storybook/test';

import {FormDecorator} from '@/components/admin/form_design/story-decorators';

import ProductFields from './ProductFields';
import {mockProductsGet} from './mocks';

type Story = StoryObj<typeof ProductFields>;

export default {
  title: 'Form design / Products / ProductFields',
  decorators: [FormDecorator],
  component: ProductFields,
  args: {
    onChange: fn(),
  },
  parameters: {
    msw: {
      handlers: [
        mockProductsGet([
          {
            url: 'http://127.0.0.1:8000/api/v2/products/42a7271c-9675-42ca-823d-459a5d8788e9',
            uuid: '42a7271c-9675-42ca-823d-459a5d8788e9',
            name: 'Local product',
            price: '100.00',
            information: '',
            producttype: null,
          },
          {
            url: 'http://127.0.0.1:8000/api/v2/products/ed1d5103-772a-4205-a14f-2958020741ec',
            uuid: 'ed1d5103-772a-4205-a14f-2958020741ec',
            name: 'Open Product product',
            price: null,
            information: '',
            producttype: 'ed1d5103-772a-4205-a14f-2958020741ec',
          },
        ]),
      ],
    },
  },
} satisfies Meta<typeof ProductFields>;

export const LocalProduct: Story = {
  play: async ({canvasElement, args}) => {
    const canvas = within(canvasElement);
    const selectInput = await canvas.findByRole('combobox', {name: 'Product'});

    await userEvent.click(selectInput);
    expect(await canvas.findByText('Local product')).toBeVisible();
    expect(await canvas.findByText('Open Product product')).toBeVisible();

    await userEvent.selectOptions(
      selectInput,
      'http://127.0.0.1:8000/api/v2/products/42a7271c-9675-42ca-823d-459a5d8788e9'
    );

    expect(args.onChange).toHaveBeenCalledWith({
      target: {
        name: 'form.product',
        value: {
          url: 'http://127.0.0.1:8000/api/v2/products/42a7271c-9675-42ca-823d-459a5d8788e9',
          producttype: null,
        },
      },
    });
  },
};

export const OpenProductProduct: Story = {
  play: async ({canvasElement, args}) => {
    const canvas = within(canvasElement);
    const selectInput = await canvas.findByRole('combobox', {name: 'Product'});

    await userEvent.click(selectInput);
    expect(await canvas.findByText('Local product')).toBeVisible();
    expect(await canvas.findByText('Open Product product')).toBeVisible();

    await userEvent.selectOptions(
      selectInput,
      'http://127.0.0.1:8000/api/v2/products/ed1d5103-772a-4205-a14f-2958020741ec'
    );

    expect(args.onChange).toHaveBeenCalledWith({
      target: {
        name: 'form.product',
        value: {
          url: 'http://127.0.0.1:8000/api/v2/products/ed1d5103-772a-4205-a14f-2958020741ec',
          producttype: 'ed1d5103-772a-4205-a14f-2958020741ec',
        },
      },
    });
  },
};
