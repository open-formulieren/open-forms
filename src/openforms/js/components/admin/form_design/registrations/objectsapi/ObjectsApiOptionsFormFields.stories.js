import {expect, fn, userEvent, waitFor, within} from '@storybook/test';
import {Form, Formik} from 'formik';

import {
  FeatureFlagsDecorator,
  FormModalContentDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';
import {rsSelect} from 'utils/storybookTestHelpers';

import ObjectsApiOptionsFormFields from './ObjectsApiOptionsFormFields';
import {
  mockCataloguesGet,
  mockDocumentTypesGet,
  mockObjecttypeVersionsGet,
  mockObjecttypesError,
  mockObjecttypesGet,
  mockTargetPathsPost,
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
  decorators: [ValidationErrorsDecorator, FeatureFlagsDecorator, FormModalContentDecorator],
  render,
  args: {
    apiGroups: [
      ['group-1', 'Objects API group 1'],
      ['group-2', 'Objects API group 2'],
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
        mockTargetPathsPost({
          string: [
            {
              targetPath: ['path', 'to.the', 'target'],
              isRequired: true,
              jsonSchema: {type: 'string'},
            },
          ],
        }),
      ],
    },
  },
};

export const Default = {};

export const SwitchToV2Empty = {
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {name: 'Variabelekoppelingen'});
    expect(v2Tab).toHaveAttribute('aria-selected', 'true');

    const groupSelect = canvas.getByLabelText('API-groep');
    await rsSelect(groupSelect, 'Objects API group 1');

    const objectTypeSelect = canvas.getByLabelText('Objecttype');
    await waitFor(() => {
      expect(objectTypeSelect).toBeVisible();
    });
    await rsSelect(objectTypeSelect, 'Tree (open)');

    const objectTypeVersionSelect = canvas.getByLabelText('Versie');
    await waitFor(() => {
      expect(objectTypeVersionSelect).toBeVisible();
    });
    await rsSelect(objectTypeVersionSelect, '2 (draft)');

    const testForm = await canvas.findByTestId('test-form');
    expect(testForm).toHaveFormValues({
      objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
      objecttypeVersion: '2',
    });
  },
};

export const SwitchToV2Existing = {
  args: {
    formData: {
      objectsApiGroup: 'group-1',
      objecttype: '2c77babf-a967-4057-9969-0200320d23f2',
      objecttypeVersion: 1,
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {name: 'Variabelekoppelingen'});
    expect(v2Tab).toHaveAttribute('aria-selected', 'true');

    const testForm = await canvas.findByTestId('test-form');

    expect(await canvas.findByText('Person (open)')).toBeVisible();
    expect(await canvas.findByText('1 (published)')).toBeVisible();
    expect(testForm).toHaveFormValues({
      objectsApiGroup: 'group-1',
      objecttype: '2c77babf-a967-4057-9969-0200320d23f2',
      objecttypeVersion: '1',
    });

    const v1Tab = canvas.getByRole('tab', {name: 'Verouderd (sjabloon)'});
    await userEvent.click(v1Tab);

    // Close the confirmation modal
    await userEvent.click(
      within(await canvas.findByRole('dialog')).getByRole('button', {
        name: 'Accepteren',
      })
    );
    await waitFor(() => {
      // Expect v1Tab to be the selected tab
      expect(v1Tab).toHaveAttribute('aria-selected', 'true');
    });

    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        objectsApiGroup: 'group-1',
        objecttype: '2c77babf-a967-4057-9969-0200320d23f2',
        objecttypeVersion: '1',
      });
    });
  },
};

export const SwitchToV2NonExisting = {
  args: {
    formData: {
      objectsApiGroup: 'group-1',
      objecttype: 'a-non-existing-uuid',
      objecttypeVersion: 1,
    },
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {name: 'Variabelekoppelingen'});
    expect(v2Tab).toHaveAttribute('aria-selected', 'true');

    const testForm = await canvas.findByTestId('test-form');
    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        objecttype: '',
        objecttypeVersion: '',
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
    const canvas = within(canvasElement);

    const v2Tab = canvas.getByRole('tab', {name: 'Variabelekoppelingen'});
    expect(v2Tab).toHaveAttribute('aria-selected', 'true');

    await step('Retrieving object types', async () => {
      const groupSelect = canvas.getByLabelText('API-groep');
      await rsSelect(groupSelect, 'Objects API group 1');

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
      [`${NAME}.authAttributePath`, 'Field is required'],
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
      [`${NAME}.authAttributePath`, 'Field is required'],
      [`${NAME}.organisatieRsin`, 'Computer says no'],
    ],
  },
};

export const SelectDocumentType = {
  args: {
    formData: {
      version: 2,
      objectsApiGroup: 'group-1',
    },
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const fieldsetTitle = canvas.getByRole('heading', {name: 'Documenttypen (Tonen)'});
    expect(fieldsetTitle).toBeVisible();
    await userEvent.click(within(fieldsetTitle).getByRole('link', {name: '(Tonen)'}));

    const catalogueSelect = canvas.getByLabelText('Catalogus');
    await rsSelect(catalogueSelect, 'Catalogus 1');
    const pdfSelect = canvas.getByLabelText('Informatieobjecttype inzendings-PDF');
    await rsSelect(pdfSelect, 'Test PDF');

    const testForm = await canvas.findByTestId('test-form');
    await waitFor(() => {
      expect(testForm).toHaveFormValues({
        iotSubmissionReport: 'Test PDF',
        iotSubmissionCsv: '',
        iotAttachment: '',
      });
    });

    await rsSelect(catalogueSelect, 'Catalogus 2');
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
      objectsApiGroup: 'group-1',
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
      objectsApiGroup: 'group-1',
      catalogue: {
        rsin: '111111111',
        domain: 'TEST',
      },
      iotSubmissionReport: 'Document type 4 with a rather long draft description',
      iotSubmissionCsv: 'Not-found documenttype',
    },
  },
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
