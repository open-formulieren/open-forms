import {useArgs} from '@storybook/preview-api';
import {expect, fn, userEvent, waitFor, within} from '@storybook/test';
import selectEvent from 'react-select-event';

import {FormDecorator} from 'components/admin/form_design/story-decorators';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';

import ObjectsApiOptionsFormFields from './ObjectsApiOptionsFormFields';
import {
  mockCatalogiGet,
  mockInformatieobjecttypenGet,
  mockObjecttypeVersionsGet,
  mockObjecttypesError,
  mockObjecttypesGet,
} from './mocks';

// WARNING
// The `render` function will mutate args, meaning interactions can't be run twice
// Be sure to refresh the page and remove the args in the query parameters

const render = ({apiGroups}) => {
  const [{formData}, updateArgs] = useArgs();
  const onChange = newValues => {
    updateArgs({formData: newValues});
  };

  return (
    <Fieldset>
      <FormRow>
        <Field name="dummy" label="">
          <ObjectsApiOptionsFormFields
            index={0}
            name="dummy"
            schema={{
              type: 'object',
              properties: {
                objectsApiGroup: {
                  type: 'integer',
                  enum: apiGroups.map(group => group[0]),
                  enumNames: apiGroups.map(group => group[1]),
                },
              },
            }}
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
    apiGroups: [
      [1, 'Objects API group 1'],
      [2, 'Objects API group 2'],
    ],
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
        mockInformatieobjecttypenGet([
          {
            url: 'https://openzaak.nl/catalogi/api/v1/informatieobjecttypen/f9a6cd4c-5f56-4f47-ad12-2e15094f917d',
            omschrijving: 'Test IOT',
            catalogusDomein: 'Test domain',
            catalogusRsin: '000000000',
            catalogusLabel: 'Test domain (RSIN: 000000000)',
            // Not available at runtime, but allows filtering with the `catalogus_url` query param:
            catalogusUrl:
              'http://openzaak.nl/catalogi/api/v1/catalogussen/7b403bcd-1f2e-4b50-8631-eec3d3a44e66',
          },
          {
            url: 'https://openzaak.nl/catalogi/api/v1/informatieobjecttypen/c2a25a12-9822-49b6-956b-89f0c39b11fe',
            omschrijving: 'Test IOT 2',
            catalogusDomein: 'Test domain 2',
            catalogusRsin: '000000000',
            catalogusLabel: 'Test domain 2 (RSIN: 000000000)',
            // Not available at runtime, but allows filtering with the `catalogus_url` query param:
            catalogusUrl:
              'http://openzaak.nl/catalogi/api/v1/catalogussen/57a48fbd-c443-43d5-bee0-9a9d0086439e',
          },
        ]),
        mockCatalogiGet([
          {
            url: 'http://openzaak.nl/catalogi/api/v1/catalogussen/7b403bcd-1f2e-4b50-8631-eec3d3a44e66',
            domein: 'Test domain',
            rsin: '000000000',
            label: 'Test domain (RSIN: 000000000)',
          },
          {
            url: 'http://openzaak.nl/catalogi/api/v1/catalogussen/57a48fbd-c443-43d5-bee0-9a9d0086439e',
            domein: 'Test domain 2',
            rsin: '000000000',
            label: 'Test domain 2 (RSIN: 000000000)',
          },
        ]),
      ],
    },
  },
};

export const Default = {};

export const SwitchToV2Empty = {
  play: async ({canvasElement}) => {
    window.confirm = fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    const groupSelect = canvas.getByLabelText('Objecten API-groep');
    const objecttypeSelect = canvas.getByLabelText('Objecttype');
    const objecttypeVersionSelect = canvas.getByLabelText('Objecttypeversie');
    await selectEvent.select(groupSelect, 'Objects API group 1');
    await selectEvent.select(objecttypeSelect, 'Tree (open)');
    await selectEvent.select(objecttypeVersionSelect, '2 (draft)');

    const v1Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v1Tab);

    expect(await canvas.findByText('Tree (open)', {exact: true})).toBeVisible();
    expect(await canvas.findByText('2 (draft)', {exact: true})).toBeVisible();
  },
};

export const SwitchToV2Existing = {
  args: {
    formData: {
      objectsApiGroup: 1,
      objecttype: '2c77babf-a967-4057-9969-0200320d23f2',
      objecttypeVersion: 1,
    },
  },
  play: async ({canvasElement}) => {
    window.confirm = fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    const groupSelect = canvas.getByLabelText('Objecten API-groep');
    await selectEvent.select(groupSelect, 'Objects API group 1');

    expect(await canvas.findByText('Person (open)', {exact: true})).toBeVisible();
    expect(await canvas.findByText('1 (published)', {exact: true})).toBeVisible();

    const v1Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v1Tab);

    expect(await canvas.findByText('Person (open)', {exact: true})).toBeVisible();
    expect(await canvas.findByText('1 (published)', {exact: true})).toBeVisible();
  },
};

export const SwitchToV2NonExisting = {
  args: {
    formData: {
      objectsApiGroup: 1,
      objecttype: 'a-non-existing-uuid',
      objecttypeVersion: 1,
    },
  },
  play: async ({canvasElement}) => {
    window.confirm = fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    const groupSelect = canvas.getByLabelText('Objecten API-groep');
    const objecttypeSelect = canvas.getByLabelText('Objecttype');
    const objecttypeVersionSelect = canvas.getByLabelText('Objecttypeversie');
    await selectEvent.select(groupSelect, 'Objects API group 1');
    await selectEvent.select(objecttypeSelect, 'Tree (open)');
    await selectEvent.select(objecttypeVersionSelect, '2 (draft)');

    const v1Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v1Tab);

    expect(await canvas.findByText('Tree (open)', {exact: true})).toBeVisible();
    expect(await canvas.findByText('2 (draft)', {exact: true})).toBeVisible();
  },
};

export const AutoSelectApiGroup = {
  args: {
    apiGroups: [[1, 'Single Objects API group']],
  },
  play: async ({canvasElement}) => {
    window.confirm = fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    await waitFor(() => {
      expect(canvas.getByText('Single Objects API group', {exact: true})).toBeVisible();
    });
  },
};

export const APIFetchError = {
  parameters: {
    msw: {
      handlers: [mockObjecttypesError()],
    },
  },
  play: async ({canvasElement}) => {
    window.confirm = fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    const groupSelect = canvas.getByLabelText('Objecten API-groep');
    await selectEvent.select(groupSelect, 'Objects API group 1');

    const errorMessage = await canvas.findByText(
      'Er ging iets fout bij het ophalen van de beschikbare objecttypen en versies.'
    );

    expect(errorMessage).toBeVisible();
  },
};

export const CatalogusSelect = {
  args: {
    formData: {
      objectsApiGroup: 1,
      objecttype: '2c77babf-a967-4057-9969-0200320d23f2',
      objecttypeVersion: 1,
    },
  },
  play: async ({canvasElement}) => {
    window.confirm = fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {selected: false});
    await userEvent.click(v2Tab);

    const catalogSelect = canvas.getByLabelText('Catalog');
    await selectEvent.select(catalogSelect, 'Test domain (RSIN: 000000000)');

    const IOTPDFSelect = canvas.getByLabelText('Informatieobjecttype inzendings-PDF');
    await selectEvent.select(IOTPDFSelect, 'Test IOT');

    await selectEvent.select(catalogSelect, 'Test domain 2 (RSIN: 000000000)');

    await selectEvent.select(IOTPDFSelect, 'Test IOT 2');
  },
};
