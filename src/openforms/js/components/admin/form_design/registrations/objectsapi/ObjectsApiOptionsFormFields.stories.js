import {useArgs} from '@storybook/preview-api';
import {expect} from '@storybook/test';
import * as test from '@storybook/test';
import {userEvent, within} from '@storybook/test';

import {FormDecorator} from 'components/admin/form_design/story-decorators';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';

import ObjectsApiOptionsFormFields from './ObjectsApiOptionsFormFields';
import {mockObjecttypeVersionsGet, mockObjecttypesError, mockObjecttypesGet} from './mocks';

// WARNING
// The `render` function will mutate args, meaning interactions can't be run twice
// Be sure to refresh the page and remove the args in the query parameters

const render = ({index, label, name}) => {
  const [{formData}, updateArgs] = useArgs();
  const onChange = newValues => {
    updateArgs({formData: newValues});
  };

  return (
    <Fieldset>
      <FormRow>
        <Field name={name} label={label}>
          <ObjectsApiOptionsFormFields
            index={index}
            name={name}
            formData={formData}
            onChange={onChange}
          />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

export default {
  title: 'Form design/Registration/Objects API',
  decorators: [FormDecorator],
  render,
  args: {
    formData: {},
  },
  parameters: {
    msw: {
      handlers: [
        mockObjecttypesGet([
          {
            url: 'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f1',
            uuid: '2c77babf-a967-4057-9969-0200320d23f1',
            name: 'Tree',
            namePlural: 'Trees',
            dataClassification: 'open',
          },
          {
            url: 'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f2',
            uuid: '2c77babf-a967-4057-9969-0200320d23f2',
            name: 'Person',
            namePlural: 'Persons',
            dataClassification: 'open',
          },
        ]),
        mockObjecttypeVersionsGet([
          {version: 1, status: 'published'},
          {version: 2, status: 'draft'},
        ]),
      ],
    },
  },
};

export const Default = {};

export const SwitchToV2Empty = {
  play: async ({canvasElement}) => {
    window.confirm = test.fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    await canvas.findByRole('option', {name: 'Tree (open)'}, {timeout: 5000});
    expect(canvas.getByLabelText('Objecttype')).toHaveValue(
      'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f1'
    );

    await canvas.findByRole('option', {name: '2 (draft)'});
    expect(canvas.getByLabelText('Objecttype version')).toHaveValue('2');

    const v1Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v1Tab);

    expect(canvas.getByLabelText('Objecttype')).toHaveValue(
      'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f1'
    );
    // This time as a number as it is a number input:
    expect(canvas.getByLabelText('Objecttype version')).toHaveValue(2);
  },
};

export const SwitchToV2Existing = {
  args: {
    formData: {
      objecttype: 'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f2',
      objecttypeVersion: 1,
    },
  },
  play: async ({canvasElement}) => {
    window.confirm = test.fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    await canvas.findByRole('option', {name: 'Person (open)'}, {timeout: 5000});
    expect(canvas.getByLabelText('Objecttype')).toHaveValue(
      'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f2'
    );

    await canvas.findByRole('option', {name: '1 (published)'});
    expect(canvas.getByLabelText('Objecttype version')).toHaveValue('1');

    const v1Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v1Tab);

    expect(canvas.getByLabelText('Objecttype')).toHaveValue(
      'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f2'
    );
    expect(canvas.getByLabelText('Objecttype version')).toHaveValue('1');
  },
};

export const SwitchToV2NonExisting = {
  args: {
    formData: {
      objecttype: 'https://objecttypen.nl/api/v1/objecttypes/a-non-existing-uuid',
      objecttypeVersion: 1,
    },
  },
  play: async ({canvasElement}) => {
    window.confirm = test.fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    await canvas.findByRole('option', {name: 'Tree (open)'}, {timeout: 5000});
    expect(canvas.getByLabelText('Objecttype')).toHaveValue(
      'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f1'
    );

    await canvas.findByRole('option', {name: '2 (draft)'});
    expect(canvas.getByLabelText('Objecttype version')).toHaveValue('2');

    const v1Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v1Tab);

    expect(canvas.getByLabelText('Objecttype')).toHaveValue(
      'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f1'
    );
    // This time as a number as it is a number input:
    expect(canvas.getByLabelText('Objecttype version')).toHaveValue(2);
  },
};

export const APIFetchError = {
  parameters: {
    msw: {
      handlers: [mockObjecttypesError()],
    },
  },
  play: async ({canvasElement}) => {
    window.confirm = test.fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    const errorMessage = await canvas.findByText(
      'Something went wrong when fectching the available Objecttypes and versions'
    );

    expect(errorMessage).toBeVisible();
  },
};
