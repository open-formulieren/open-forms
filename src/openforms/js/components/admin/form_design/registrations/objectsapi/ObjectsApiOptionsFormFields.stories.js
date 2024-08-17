import {expect, fn, userEvent, waitFor, within} from '@storybook/test';
import {Form, Formik} from 'formik';
import selectEvent from 'react-select-event';

import {ValidationErrorsDecorator} from 'components/admin/form_design/story-decorators';
import {FeatureFlagsDecorator} from 'components/admin/form_design/story-decorators';

import ObjectsApiOptionsFormFields from './ObjectsApiOptionsFormFields';
import {
  mockCataloguesGet,
  mockDocumentTypesGet,
  mockObjecttypeVersionsGet,
  mockObjecttypesError,
  mockObjecttypesGet,
} from './mocks';

const NAME = 'form.registrationBackends.0.options';

const render = ({apiGroups, formData}) => (
  <Formik initialValues={formData} onSubmit={fn()}>
    <Form data-testid="test-form">
      <ObjectsApiOptionsFormFields index={0} name={NAME} apiGroupChoices={apiGroups} />
    </Form>
  </Formik>
);

export default {
  title: 'Form design/Registration/Objects API',
  decorators: [ValidationErrorsDecorator],
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
        mockCataloguesGet(),
        mockDocumentTypesGet(),
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
    await selectEvent.select(groupSelect, 'Objects API group 1');

    const testForm = await canvas.findByTestId('test-form');
    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
        objecttypeVersion: '2',
      });
    });
    expect(canvas.getByText('Tree (open)')).toBeVisible();
    expect(canvas.getByText('2 (draft)')).toBeVisible();

    const v1Tab = canvas.getByRole('tab', {name: 'Verouderd (sjabloon)'});
    await userEvent.click(v1Tab);
    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
        objecttypeVersion: '2',
      });
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

    const testForm = await canvas.findByTestId('test-form');

    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        objectsApiGroup: '1',
        objecttype: '2c77babf-a967-4057-9969-0200320d23f2',
        objecttypeVersion: '1',
      });
    });
    expect(canvas.getByText('Person (open)')).toBeVisible();
    expect(canvas.getByText('1 (published)')).toBeVisible();

    const v1Tab = canvas.getByRole('tab', {name: 'Verouderd (sjabloon)'});
    await userEvent.click(v1Tab);
    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        objectsApiGroup: '1',
        objecttype: '2c77babf-a967-4057-9969-0200320d23f2',
        objecttypeVersion: '1',
      });
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

    const testForm = await canvas.findByTestId('test-form');
    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
        objecttypeVersion: '2',
      });
    });
    expect(canvas.getByText('Tree (open)')).toBeVisible();
    expect(canvas.getByText('2 (draft)')).toBeVisible();

    const v1Tab = canvas.getByRole('tab', {name: 'Verouderd (sjabloon)'});
    await userEvent.click(v1Tab);
    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
        objecttypeVersion: '2',
      });
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
  play: async ({canvasElement, step}) => {
    window.confirm = fn(() => true);
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {name: 'Variabelekoppelingen'});
    await userEvent.click(v2Tab);

    await step('Retrieving object types', async () => {
      const groupSelect = canvas.getByLabelText('API-groep');
      await selectEvent.select(groupSelect, 'Objects API group 1');

      const errorMessage = await canvas.findByText(
        'Er ging iets fout bij het ophalen van de objecttypes.'
      );
      expect(errorMessage).toBeVisible();
    });

    await step('Retrieving catalogues and document types', async () => {
      const errorMessage = await canvas.findByText(
        'Er ging iets fout bij het ophalen van de beschikbare catalogi en/of documenttypen.'
      );
      expect(errorMessage).toBeVisible();
    });
  },
};

export const V1ValidationErrors = {
  args: {
    formData: {
      version: 1,
    },
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
    formData: {
      version: 2,
    },
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

export const SelectDocumentType = {
  args: {
    formData: {
      version: 2,
      objectsApiGroup: 1,
    },
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const fieldsetTitle = canvas.getByRole('heading', {name: 'Documenttypen (Tonen)'});
    expect(fieldsetTitle).toBeVisible();
    await userEvent.click(within(fieldsetTitle).getByRole('link', {name: '(Tonen)'}));

    const catalogueSelect = canvas.getByLabelText('Catalogus');
    await selectEvent.select(catalogueSelect, 'Catalogus 1');
    const pdfSelect = canvas.getByLabelText('Informatieobjecttype inzendings-PDF');
    await selectEvent.select(pdfSelect, 'Test PDF');

    const testForm = await canvas.findByTestId('test-form');
    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        iotSubmissionReport: 'Test PDF',
        iotSubmissionCsv: '',
        iotAttachment: '',
      });
    });

    await selectEvent.select(catalogueSelect, 'Catalogus 2');
    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        iotSubmissionReport: '',
        iotSubmissionCsv: '',
        iotAttachment: '',
      });
    });
  },
};

export const DisplayPersistedConfiguration = {
  args: {
    formData: {
      version: 2,
      objectsApiGroup: 1,
      catalogue: {
        rsin: '000000000',
        domain: 'TEST',
      },
      iotSubmissionReport: 'Test PDF',
    },
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const fieldsetTitle = canvas.getByRole('heading', {name: 'Documenttypen (Tonen)'});
    expect(fieldsetTitle).toBeVisible();
    await userEvent.click(within(fieldsetTitle).getByRole('link', {name: '(Tonen)'}));

    expect(await canvas.findByText('Catalogus 1')).toBeVisible();
    expect(await canvas.findByText('Test PDF')).toBeVisible();
  },
};

export const DraftDocumentTypesFeatureFlagOn = {
  args: {
    formData: {
      version: 2,
      objectsApiGroup: 1,
      catalogue: {
        rsin: '111111111',
        domain: 'TEST',
      },
      iotSubmissionReport: 'A rather long draft description',
      iotSubmissionCsv: 'Not-found documenttype',
    },
  },
  decorators: [FeatureFlagsDecorator],
  parameters: {
    featureFlags: {
      ZGW_APIS_INCLUDE_DRAFTS: true,
    },
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const fieldsetTitle = canvas.getByRole('heading', {name: 'Documenttypen (Tonen)'});
    expect(fieldsetTitle).toBeVisible();
    await userEvent.click(within(fieldsetTitle).getByRole('link', {name: '(Tonen)'}));
  },
};
