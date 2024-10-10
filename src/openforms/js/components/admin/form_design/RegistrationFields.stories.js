import {expect, fn, screen, userEvent, waitFor, within} from '@storybook/test';
import selectEvent from 'react-select-event';

import {
  mockDocumentTypesGet,
  mockCataloguesGet as mockObjectsApiCataloguesGet,
  mockObjecttypeVersionsGet,
  mockObjecttypesGet,
} from 'components/admin/form_design/registrations/objectsapi/mocks';
import {
  mockCaseTypesGet,
  mockCataloguesGet as mockZGWApisCataloguesGet,
} from 'components/admin/form_design/registrations/zgw/mocks';
import {
  FormDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';

import RegistrationFields from './RegistrationFields';

export default {
  title: 'Form design / Registration / RegistrationFields',
  decorators: [ValidationErrorsDecorator, FormDecorator],
  component: RegistrationFields,
  args: {
    availableBackends: [
      {
        id: 'demo',
        label: 'Demo - print to console',
        schema: {
          properties: {
            extraLine: {
              minLength: 1,
              title: 'Extra print statement',
              type: 'string',
            },
          },
          type: 'object',
        },
      },
      {
        id: 'zgw-create-zaak',
        label: "ZGW API's",
        // real schema is defined, but irrelevant because of our react components
        schema: {
          type: 'object',
          properties: {
            zgwApiGroup: {
              enum: [1],
              enumNames: ['ZGW API group 1'],
            },
            zaakVertrouwelijkheidaanduiding: {
              enum: ['openbaar', 'geheim'],
              enumNames: ['Openbaar', 'Geheim'],
            },
          },
        },
      },
      {
        id: 'stuf-zds-create-zaak',
        label: 'StUF-ZDS',
        // real schema is defined, but irrelevant because of our react components
        schema: {
          type: 'object',
          properties: {
            zdsZaaktypeCode: {
              type: 'string',
              minLength: 1,
              title: 'Zds zaaktype code',
              description: 'Zaaktype code for newly created Zaken in StUF-ZDS',
            },
            zdsZaaktypeOmschrijving: {
              type: 'string',
              minLength: 1,
              title: 'Zds zaaktype omschrijving',
              description: 'Zaaktype description for newly created Zaken in StUF-ZDS',
            },
            zdsZaaktypeStatusCode: {
              type: 'string',
              minLength: 1,
              title: 'Zds zaaktype status code',
              description: 'Zaaktype status code for newly created zaken in StUF-ZDS',
            },
            zdsZaaktypeStatusOmschrijving: {
              type: 'string',
              minLength: 1,
              title: 'Zds zaaktype status omschrijving',
              description: 'Zaaktype status omschrijving for newly created zaken in StUF-ZDS',
            },
            zdsDocumenttypeOmschrijvingInzending: {
              type: 'string',
              minLength: 1,
              title: 'Zds documenttype omschrijving inzending',
              description: 'Documenttype description for newly created zaken in StUF-ZDS',
            },
            zdsZaakdocVertrouwelijkheid: {
              type: 'string',
              enum: [
                'ZEER GEHEIM',
                'GEHEIM',
                'CONFIDENTIEEL',
                'VERTROUWELIJK',
                'ZAAKVERTROUWELIJK',
                'INTERN',
                'BEPERKT OPENBAAR',
                'OPENBAAR',
              ],
              enumNames: [
                'Zeer geheim',
                'Geheim',
                'Confidentieel',
                'Vertrouwelijk',
                'Zaakvertrouwelijk',
                'Intern',
                'Beperkt openbaar',
                'Openbaar',
              ],
              title: 'Document confidentiality level',
              description:
                'Indication of the level to which extend the dossier of the ZAAK is meant to be public. This is set on the documents created for the ZAAK.',
            },
            paymentStatusUpdateMapping: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  formVariable: {
                    type: 'string',
                    minLength: 1,
                    title: 'Form variable',
                    description: 'The name of the form variable to be mapped',
                  },
                  stufName: {
                    type: 'string',
                    minLength: 1,
                    title: 'StUF-ZDS name',
                    description: 'The name in StUF-ZDS to which the form variable should be mapped',
                  },
                },
                required: ['formVariable', 'stufName'],
              },
              title: 'payment status update variable mapping',
              description:
                'This mapping is used to map the variable keys to keys used in the XML that is sent to StUF-ZDS. Those keys and the values belonging to them in the submission data are included in extraElementen.',
              default: [
                {
                  formVariable: 'payment_completed',
                  stufName: 'payment_completed',
                },
                {
                  formVariable: 'payment_amount',
                  stufName: 'payment_amount',
                },
                {
                  formVariable: 'payment_public_order_ids',
                  stufName: 'payment_public_order_ids',
                },
                {
                  formVariable: 'provider_payment_ids',
                  stufName: 'provider_payment_ids',
                },
              ],
            },
          },
        },
      },
      {
        id: 'email',
        label: 'Email registration',
        schema: {
          properties: {
            attachFilesToEmail: {
              description:
                'Enable to attach file uploads to the registration email. If set, this overrides the global default. Form designers should take special care to ensure that the total file upload sizes do not exceed the email size limit.',
              enum: [null, true, false],
              enumNames: ['(use global default)', 'yes', 'no'],
              title: 'attach files to email',
              type: ['boolean', 'null'],
            },
            attachmentFormats: {
              items: {
                enum: ['pdf', 'csv', 'xlsx'],
                enumNames: ['PDF', 'CSV', 'Excel'],
                type: 'string',
              },
              title: 'The format(s) of the attachment(s) containing the submission details',
              type: 'array',
            },
            emailContentTemplateHtml: {
              description: 'Content of the registration email message (as text).',
              minLength: 1,
              title: 'email content template HTML',
              type: 'string',
            },
            emailContentTemplateText: {
              description: 'Content of the registration email message (as text).',
              minLength: 1,
              title: 'email content template text',
              type: 'string',
            },
            emailPaymentSubject: {
              description:
                'Subject of the email sent to the registration backend to notify a change in the payment status.',
              minLength: 1,
              title: 'email payment subject',
              type: 'string',
            },
            emailSubject: {
              description:
                "Subject of the email sent to the registration backend. You can use the expressions '{{ form_name }}' and '{{ public_reference }}' to include the form name and the reference number to the submission in the subject.",
              minLength: 1,
              title: 'email subject',
              type: 'string',
            },
            paymentEmails: {
              items: {
                format: 'email',
                minLength: 1,
                type: 'string',
              },
              title:
                'The email addresses to which the payment status update will be sent (defaults to general registration addresses)',
              type: 'array',
            },
            toEmails: {
              items: {
                format: 'email',
                minLength: 1,
                type: 'string',
              },
              title: 'The email addresses to which the submission details will be sent',
              type: 'array',
            },
          },
          required: ['toEmails'],
          type: 'object',
        },
      },
      {
        id: 'objects_api',
        label: 'Objects API registration',
        // real schema is defined, but irrelevant because of our react components
        schema: {
          type: 'object',
          properties: {
            objectsApiGroup: {
              enum: [1],
              enumNames: ['Objects API Group'],
            },
          },
        },
      },
      {
        id: 'microsoft-graph',
        label: 'Microsoft Graph (OneDrive/SharePoint)',
        schema: {
          properties: {
            driveId: {
              description: 'ID of the drive to use. If left empty, the default drive will be used.',
              minLength: 1,
              title: 'drive ID',
              type: 'string',
            },
            folderPath: {
              description:
                'The path of the folder where folders containing Open-Forms related documents will be created. You can use the expressions {{ year }}, {{ month }} and {{ day }}. It should be an absolute path - i.e. it should start with /',
              minLength: 1,
              title: 'folder path',
              type: 'string',
            },
          },
          type: 'object',
        },
      },
      {
        id: 'camunda',
        label: 'Camunda',
        // real schema is defined, but irrelevant because of our react components
        schema: {
          type: 'object',
          properties: {},
        },
      },
    ],
    configuredBackends: [],
    onChange: fn(),
    addBackend: fn(),
    onDelete: fn(),
    availableComponents: {
      textField1: {
        label: 'textfield1',
      },
      textField2: {
        label: 'textfield2',
      },
    },
  },
  parameters: {
    msw: {
      handlers: {
        objectTypesMocks: [
          mockObjecttypesGet([
            {
              url: 'https://objecttypen.nl/api/v1/objecttypes/d89f3a0e-096b-45ea-afe1-ce211d63d1f2',
              uuid: 'd89f3a0e-096b-45ea-afe1-ce211d63d1f2',
              name: 'Tree',
              namePlural: 'Trees',
              dataClassification: 'open',
            },
          ]),
          mockObjecttypeVersionsGet([
            {version: 1, status: 'published'},
            {version: 2, status: 'draft'},
          ]),
          mockObjectsApiCataloguesGet(),
          mockDocumentTypesGet(),
        ],
        zgwMocks: [mockZGWApisCataloguesGet(), mockCaseTypesGet()],
      },
    },
  },
};

const OZ_BASE = 'https://test.openzaak.nl/catalogi/api/v1/';

export const ConfiguredBackends = {
  args: {
    configuredBackends: [
      {
        key: 'backend1',
        name: 'Demo',
        backend: 'demo',
        options: {extraLine: 'Filled out option'},
      },
      {
        key: 'backend2',
        name: "ZGW API's",
        backend: 'zgw-create-zaak',
        options: {
          zgwApiGroup: 1,
          zaaktype: `${OZ_BASE}zaaktypen/7fc0ed69`,
          informatieobjecttype: `${OZ_BASE}informatieobjecttypen/89ecd526`,
          organisatieRsin: '',
          zaakVertrouwelijkheidaanduiding: '',
          medewerkerRoltype: '',
          objecttype: '',
          objecttypeVersion: '',
          contentJson: '',
          propertyMappings: [],
        },
      },
      {
        key: 'backend3',
        name: 'Email',
        backend: 'email',
        options: {
          toEmails: ['noreply@opengem.nl'],
          attachmentFormats: [],
          paymentEmails: [],
          attachFilesToEmail: false,
          email_subject: '',
          email_payment_subject: '',
          email_content_template_html: '',
          email_content_template_text: '',
        },
      },
      {
        key: 'backend4',
        name: 'Objects API',
        backend: 'objects_api',
        options: {
          version: 2,
          objectsApiGroup: 1,
          objecttype: 'd89f3a0e-096b-45ea-afe1-ce211d63d1f2',
          objecttypeVersion: 1,
          updateExistingObject: false,
          informatieobjecttypeSubmissionReport: '',
          uploadSubmissionCsv: false,
          informatieobjecttypeSubmissionCsv: '',
          informatieobjecttypeAttachment: '',
          organisatieRsin: '',
          variablesMapping: [],
          geometryVariableKey: '',
        },
      },
      {
        key: 'backend5',
        name: 'Sharepoint',
        backend: 'microsoft-graph',
        options: {
          driveId: '',
          folderPath: '',
        },
      },
      {
        key: 'backend6',
        name: 'StUF ZDS',
        backend: 'stuf-zds-create-zaak',
        options: {
          paymentStatusUpdateMapping: [
            {
              formVariable: 'payment_completed',
              stufName: 'payment_completed',
            },
            {
              formVariable: 'payment_amount',
              stufName: 'payment_amount',
            },
            {
              formVariable: 'payment_public_order_ids',
              stufName: 'payment_public_order_ids',
            },
            {
              formVariable: 'provider_payment_ids',
              stufName: 'provider_payment_ids',
            },
          ],
          zdsDocumenttypeOmschrijvingInzending: '',
          zdsZaakdocVertrouwelijkheid: 'OPENBAAR',
          zdsZaaktypeCode: '',
          zdsZaaktypeOmschrijving: '',
          zdsZaaktypeStatusCode: '',
          zdsZaaktypeStatusOmschrijving: '',
        },
      },
    ],
    validationErrors: [
      ['form.registrationBackends.1.options.zgwApiGroup', 'You sure about this?'],
      ['form.registrationBackends.3.options.objectsApiGroup', 'You shall not pass.'],
    ],
  },
};

export const ObjectsAPI = {
  args: {
    configuredBackends: [
      {
        key: 'backend4',
        name: 'Objects API',
        backend: 'objects_api',
        options: {
          version: 2,
          objectsApiGroup: 1,
          objecttype: 'd89f3a0e-096b-45ea-afe1-ce211d63d1f2',
          objecttypeVersion: 1,
          updateExistingObject: false,
          informatieobjecttypeSubmissionReport: '',
          uploadSubmissionCsv: false,
          informatieobjecttypeSubmissionCsv: '',
          informatieobjecttypeAttachment: '',
          organisatieRsin: '',
          variablesMapping: [],
          geometryVariableKey: '',
        },
      },
    ],
  },

  play: async ({canvasElement, step, args}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));

    // check that the sole api group is automatically selected
    const modalForm = await screen.findByTestId('modal-form');
    expect(modalForm).toBeVisible();
    expect(modalForm).toHaveFormValues({objectsApiGroup: '1'});
    const modal = within(modalForm);

    await waitFor(() => {
      expect(modalForm).toHaveFormValues({
        objecttype: 'd89f3a0e-096b-45ea-afe1-ce211d63d1f2',
        objecttypeVersion: '1',
      });
    });

    await step('Select a catalogue for document types', async () => {
      const fieldsetTitle = modal.getByRole('heading', {name: 'Documenttypen (Tonen)'});
      expect(fieldsetTitle).toBeVisible();
      await userEvent.click(within(fieldsetTitle).getByRole('link', {name: '(Tonen)'}));

      const catalogueSelect = modal.getByLabelText('Catalogus');
      await selectEvent.select(catalogueSelect, 'Catalogus 2');
    });

    await step('Submit the form', async () => {
      await userEvent.click(modal.getByRole('button', {name: 'Opslaan'}));
      expect(args.onChange).toHaveBeenCalled();
      const call = args.onChange.mock.calls[0][0];
      const {catalogue} = call.target.value;
      expect(catalogue).toMatchObject({
        rsin: '000000000',
        domain: 'OTHER',
      });
    });

    // re-open modal for visual regression testing snapshots
    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));
  },
};

export const ObjectsAPILegacy = {
  name: 'Objects API (legacy)',
  args: {
    configuredBackends: [
      {
        key: 'backend4',
        name: 'Objects API',
        backend: 'objects_api',
        options: {
          version: 1,
          objectsApiGroup: 1,
          objecttype: 'd89f3a0e-096b-45ea-afe1-ce211d63d1f2',
          objecttypeVersion: 1,
          updateExistingObject: false,
          productaanvraagType: 'productAanvraag',
          informatieobjecttypeSubmissionReport: 'https://example.com/api/v1/iot/123',
          uploadSubmissionCsv: true,
          informatieobjecttypeSubmissionCsv: 'https://example.com/api/v1/iot/123',
          informatieobjecttypeAttachment: 'https://example.com/api/v1/iot/123',
          organisatieRsin: '123456782',
          contentJson: '{% json_summary %}',
          paymentStatusUpdateJson: '{% json_summary %}',
        },
      },
    ],
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));

    // check that the sole api group is automatically selected
    const modalForm = await screen.findByTestId('modal-form');
    expect(modalForm).toBeVisible();
    expect(modalForm).toHaveFormValues({objectsApiGroup: '1'});

    await waitFor(() => {
      expect(modalForm).toHaveFormValues({
        objecttype: 'd89f3a0e-096b-45ea-afe1-ce211d63d1f2',
        objecttypeVersion: '1',
      });
    });
  },
};

export const ZGW = {
  args: {
    configuredBackends: [
      {
        key: 'backend2',
        name: "ZGW API's",
        backend: 'zgw-create-zaak',
        options: {
          zgwApiGroup: 1,
          zaaktype: `${OZ_BASE}zaaktypen/7fc0ed69`,
          informatieobjecttype: `${OZ_BASE}informatieobjecttypen/89ecd526`,
          organisatieRsin: '',
          zaakVertrouwelijkheidaanduiding: '',
          medewerkerRoltype: '',
          objecttype: '',
          objecttypeVersion: '',
          contentJson: '',
          propertyMappings: [],
        },
      },
    ],
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));
  },
};

export const Email = {
  args: {
    configuredBackends: [
      {
        key: 'backend3',
        name: 'Email',
        backend: 'email',
        options: {
          toEmails: ['noreply@opengem.nl'],
          attachmentFormats: [],
          paymentEmails: [],
          attachFilesToEmail: false,
          email_subject: '',
          email_payment_subject: '',
          email_content_template_html: '',
          email_content_template_text: '',
        },
      },
    ],
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));
  },
};

export const STUFZDS = {
  name: 'StUF ZDS',
  args: {
    configuredBackends: [
      {
        key: 'backend6',
        name: 'StUF ZDS',
        backend: 'stuf-zds-create-zaak',
        options: {
          paymentStatusUpdateMapping: [
            {
              formVariable: 'payment_completed',
              stufName: 'payment_completed',
            },
            {
              formVariable: 'payment_amount',
              stufName: 'payment_amount',
            },
            {
              formVariable: 'payment_public_order_ids',
              stufName: 'payment_public_order_ids',
            },
            {
              formVariable: 'provider_payment_ids',
              stufName: 'provider_payment_ids',
            },
          ],
          zdsDocumenttypeOmschrijvingInzending: '',
          zdsZaakdocVertrouwelijkheid: 'OPENBAAR',
          zdsZaaktypeCode: '',
          zdsZaaktypeOmschrijving: '',
          zdsZaaktypeStatusCode: '',
          zdsZaaktypeStatusOmschrijving: '',
        },
      },
    ],
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));
  },
};
