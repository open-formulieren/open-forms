import {expect, fn, userEvent, waitFor, within} from '@storybook/test';
import {Form, Formik} from 'formik';

import {
  FormDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';

import ObjectsApiOptionsFormFields from './ObjectsApiOptionsFormFields';
import {mockObjecttypeVersionsGet, mockObjecttypesError, mockObjecttypesGet} from './mocks';

const NAME = 'form.registrationBackends.0.options';

const render = ({apiGroups, formData}) => (
  <Formik initialValues={formData} onSubmit={fn()}>
    <Form>
      <ObjectsApiOptionsFormFields index={0} name={NAME} apiGroupChoices={apiGroups} />
    </Form>
  </Formik>
);

export default {
  title: 'Form design/Registration/Objects API',
  decorators: [ValidationErrorsDecorator, FormDecorator],
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
      ],
    },
  },
};

export const Default = {};

export const SwitchToV2Empty = {
  play: async ({canvasElement}) => {
    window.confirm = fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {name: 'Variabelekoppelingen'});
    await userEvent.click(v2Tab);

    const groupSelect = canvas.getByLabelText('API-groep');
    await userEvent.selectOptions(groupSelect, 'Objects API group 1');

    await canvas.findByRole('option', {name: 'Tree (open)'}, {timeout: 5000});
    expect(canvas.getByLabelText('Objecttype')).toHaveValue('2c77babf-a967-4057-9969-0200320d23f1');

    await canvas.findByRole('option', {name: '2 (draft)'});
    expect(canvas.getByLabelText('Versie')).toHaveValue('2');

    const v1Tab = canvas.getByRole('tab', {name: 'Verouderd (sjabloon)'});
    await userEvent.click(v1Tab);

    await waitFor(() => {
      expect(canvas.getByLabelText('Objecttype')).toHaveValue(
        '2c77babf-a967-4057-9969-0200320d23f1'
      );
      expect(canvas.getByLabelText('Versie')).toHaveValue('2');
    });
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

    const v2Tab = canvas.getByRole('tab', {name: 'Variabelekoppelingen'});
    await userEvent.click(v2Tab);

    const groupSelect = canvas.getByLabelText('API-groep');
    expect(groupSelect).toHaveValue('1');

    await canvas.findByRole('option', {name: 'Person (open)'}, {timeout: 5000});
    expect(canvas.getByLabelText('Objecttype')).toHaveValue('2c77babf-a967-4057-9969-0200320d23f2');

    await canvas.findByRole('option', {name: '1 (published)'});
    expect(canvas.getByLabelText('Versie')).toHaveValue('1');

    const v1Tab = canvas.getByRole('tab', {name: 'Verouderd (sjabloon)'});
    await userEvent.click(v1Tab);

    await waitFor(() => {
      expect(canvas.getByLabelText('Objecttype')).toHaveValue(
        '2c77babf-a967-4057-9969-0200320d23f2'
      );
      expect(canvas.getByLabelText('Versie')).toHaveValue('1');
    });
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

    const v2Tab = canvas.getByRole('tab', {name: 'Variabelekoppelingen'});
    await userEvent.click(v2Tab);

    await canvas.findByRole('option', {name: 'Tree (open)'}, {timeout: 5000});
    expect(canvas.getByLabelText('Objecttype')).toHaveValue('2c77babf-a967-4057-9969-0200320d23f1');

    await canvas.findByRole('option', {name: '2 (draft)'});
    await waitFor(() => {
      expect(canvas.getByLabelText('Versie')).toHaveValue('2');
    });

    const v1Tab = canvas.getByRole('tab', {name: 'Verouderd (sjabloon)'});
    await userEvent.click(v1Tab);

    await waitFor(() => {
      expect(canvas.getByLabelText('Objecttype')).toHaveValue(
        '2c77babf-a967-4057-9969-0200320d23f1'
      );
      expect(canvas.getByLabelText('Versie')).toHaveValue('2');
    });
  },
};

export const APIFetchError = {
  parameters: {
    msw: {
      handlers: [mockObjecttypesError()],
    },
    test: {
      dangerouslyIgnoreUnhandledErrors: true, // error boundary handles it
    },
  },
  play: async ({canvasElement}) => {
    window.confirm = fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {name: 'Variabelekoppelingen'});
    await userEvent.click(v2Tab);

    const groupSelect = canvas.getByLabelText('API-groep');
    await userEvent.selectOptions(groupSelect, 'Objects API group 1');

    const errorMessage = await canvas.findByText(
      'Er ging iets fout bij het ophalen van de objecttypes.'
    );

    expect(errorMessage).toBeVisible();
  },
};

export const V1ValidationErrors = {
  args: {
    validationErrors: [
      [`${NAME}.objectsApiGroup`, 'Computer says no'],
      [`${NAME}.objecttype`, 'Computer says no'],
      [`${NAME}.objecttypeVersion`, 'Computer says no'],
      [`${NAME}.productaanvraagType`, 'Computer says no'],
      [`${NAME}.contentJson`, 'Computer says no'],
      [`${NAME}.paymentStatusUpdateJson`, 'Computer says no'],
      [`${NAME}.informatieobjecttypeSubmissionReport`, 'Computer says no'],
      [`${NAME}.informatieobjecttypeSubmissionCsv`, 'Computer says no'],
      [`${NAME}.informatieobjecttypeAttachment`, 'Computer says no'],
      [`${NAME}.organisatieRsin`, 'Computer says no'],
    ],
  },
};

export const V2ValidationErrors = {
  args: {
    validationErrors: [
      [`${NAME}.objectsApiGroup`, 'Some API-group error'],
      [`${NAME}.objecttype`, 'Computer says no'],
      [`${NAME}.objecttypeVersion`, 'Computer says no'],
      [`${NAME}.informatieobjecttypeSubmissionReport`, 'Computer says no'],
      [`${NAME}.informatieobjecttypeSubmissionCsv`, 'Computer says no'],
      [`${NAME}.informatieobjecttypeAttachment`, 'Computer says no'],
      [`${NAME}.organisatieRsin`, 'Computer says no'],
    ],
  },
};
