import type {Meta, StoryObj} from '@storybook/react-vite';
import {expect, fn, userEvent, within} from 'storybook/test';

import {FormDecorator} from '@/components/admin/form_design/story-decorators';

import PriceLogic from './PriceLogic';

type Story = StoryObj<typeof PriceLogic>;

export default {
  title: 'Form design / Products / PriceLogic',
  decorators: [FormDecorator],
  component: PriceLogic,
  args: {
    variableKey: '',
    onFieldChange: fn(),
    isOpenProduct: false,
  },
} satisfies Meta<typeof PriceLogic>;

export const LocalProduct: Story = {
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);
    const input = canvas.getByRole('combobox', {name: 'Mode'});

    await userEvent.click(input);
    expect(await canvas.findByText('Use linked product price')).toBeVisible();
    expect(await canvas.findByText('Use a variable for the price')).toBeVisible();
  },
};

export const OpenProductProduct: Story = {
  args: {
    isOpenProduct: true,
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);
    const input = canvas.getByRole('combobox', {name: 'Mode'});

    await userEvent.click(input);
    expect(await canvas.findByText('Use linked product price')).toBeVisible();
    expect(canvas.queryByText('Use a variable for the price')).toBeNull();

    // Note that the warning text is only shown when the icon is hovered over hence the
    // the .not.toBeVisible usage.
    expect(
      await canvas.findByText(
        'Only "Use linked product price" mode is allowed when a Open Product product is selected.'
      )
    ).not.toBeVisible();
  },
};
