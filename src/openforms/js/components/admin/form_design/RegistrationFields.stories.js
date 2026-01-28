import {expect, fn, screen, userEvent, waitFor, within} from 'storybook/test';

import {mockProcessDefinitionsGet} from 'components/admin/form_design/registrations/camunda/mocks';
import {
  mockDocumentTypesGet,
  mockCataloguesGet as mockObjectsApiCataloguesGet,
  mockObjecttypeVersionsGet,
  mockObjecttypesGet,
  mockTargetPathsPost,
} from 'components/admin/form_design/registrations/objectsapi/mocks';
import {
  mockCaseTypesGet,
  mockCataloguesGet as mockZGWApisCataloguesGet,
  mockDocumenTypesGet as mockZGWApisDocumenTypesGet,
  mockProductsGet as mockZGWApisProductsGet,
  mockRoleTypesGet as mockZGWApisRoleTypesGet,
} from 'components/admin/form_design/registrations/zgw/mocks';
import {
  AdminChangeFormDecorator,
  FormDecorator,
  FormModalContentDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';
import {rsSelect} from 'utils/storybookTestHelpers';

import RegistrationFields from './RegistrationFields';
import {mockFormJsonSchemaGet} from './mocks';

export default {
  title: 'Form design / Registration / RegistrationFields',
  decorators: [
    ValidationErrorsDecorator,
    FormDecorator,
    AdminChangeFormDecorator,
    FormModalContentDecorator,
  ],
  component: RegistrationFields,
  args: {
    availableBackends: [
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
            objectsApiGroup: {
              enum: ['objects-group'],
              enumNames: ['Objects API Group'],
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
            variablesMapping: {
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
              title: 'Variables mapping',
              description:
                'This mapping is used to map the variable keys (User defined variables are also available) to keys used in the XML that is sent to StUF-ZDS. Those keys and the values belonging to them in the submission data are included in extraElementen.',
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
              enum: ['objects-group'],
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
        schema: {
          type: 'object',
          properties: {
            processDefinition: {
              type: 'string',
              minLength: 1,
              title: 'Process definition',
              description: 'The process definition for which to start a process instance.',
            },
            processDefinitionVersion: {
              type: ['integer', 'null'],
              title: 'Process definition version',
              description:
                'Which version of the process definition to start. The latest version is used if not specified.',
            },
            processVariables: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  enabled: {
                    type: 'boolean',
                    title: 'enable',
                    description: 'Only enabled variables are passed into the process',
                  },
                  componentKey: {
                    type: 'string',
                    minLength: 1,
                    title: 'Component key',
                    description: 'Key of the Formio.js component to take the value from.',
                  },
                  alias: {
                    type: 'string',
                    title: 'Alias',
                    description:
                      'If provided, the Camunda process variable will have this alias as name instead of the component key. Use this to map a component onto a different process variable name.',
                  },
                },
                required: ['enabled', 'componentKey'],
                title: 'Mapped process variables',
              },
              title: 'Mapped process variables',
            },
            complexProcessVariables: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  enabled: {
                    type: 'boolean',
                    title: 'enable',
                    description: 'Only enabled variables are passed into the process',
                  },
                  alias: {
                    type: 'string',
                    minLength: 1,
                    title: 'Alias',
                    description:
                      'Name of the variable in the Camunda process instance. For complex variables, the name must be supplied.',
                  },
                  type: {
                    type: 'string',
                    enum: ['object', 'array'],
                    enumNames: ['Object', 'Array'],
                    title: 'Type',
                    description: 'The type determines how to interpret the variable definition.',
                  },
                },
                required: ['enabled', 'alias', 'type'],
                title: 'Complex process variables',
              },
              title: 'Complex process variables',
            },
          },
          required: ['processDefinition', 'processVariables', 'complexProcessVariables'],
        },
      },
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
        id: 'failing-demo',
        label: 'Demo - fail registration',
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
        id: 'exception-demo',
        label: 'Demo - exception during registration',
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
        id: 'json_dump',
        label: 'Generic JSON registration',
        schema: {
          type: 'object',
          properties: {
            service: {
              enum: [1, 2],
              enumNames: ['Service 1', 'Service 2'],
            },
            path: {
              minLength: 1,
              title: 'Relative API endpoint',
              type: 'string',
            },
            variables: {
              type: 'array',
              title: 'List of form variables',
              items: {
                type: 'string',
                title: 'form variable',
                minLength: 1,
              },
            },
          },
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
    availableFormVariables: [
      {
        dataFormat: '',
        dataType: 'string',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'textField1',
        name: 'textfield1',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'component',
      },
      {
        dataFormat: '',
        dataType: 'string',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'textField2',
        name: 'textfield2',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'component',
      },
      {
        dataFormat: '',
        dataType: 'string',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'userDefinedVar1',
        name: 'User defined string',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'user_defined',
      },
      {
        dataFormat: '',
        dataType: 'array',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: [],
        isSensitiveData: false,
        key: 'userDefinedVar2',
        name: 'User defined array',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'user_defined',
      },
      {
        dataFormat: '',
        dataType: 'float',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: null,
        isSensitiveData: false,
        key: 'userDefinedVar3',
        name: 'User defined float',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'user_defined',
      },
    ],
    registrationPluginsVariables: [
      {
        pluginIdentifier: 'stuf-zds-create-zaak',
        pluginVerboseName: 'StUF-ZDS',
        pluginVariables: [
          {
            form: null,
            formDefinition: null,
            name: 'Payment completed',
            key: 'payment_completed',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'boolean',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
          {
            form: null,
            formDefinition: null,
            name: 'Payment amount',
            key: 'payment_amount',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'float',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
          {
            form: null,
            formDefinition: null,
            name: 'Payment public order IDs',
            key: 'payment_public_order_ids',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'array',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
          {
            form: null,
            formDefinition: null,
            name: 'Provider payment IDs',
            key: 'provider_payment_ids',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'array',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
        ],
      },
      {
        pluginIdentifier: 'json_dump',
        pluginVerboseName: 'Generic JSON registration',
        pluginVariables: [
          {
            form: null,
            formDefinition: null,
            name: 'Public reference',
            key: 'public_reference',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'string',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
          {
            form: null,
            formDefinition: null,
            name: 'Form version',
            key: 'form_version',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'string',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
          {
            form: null,
            formDefinition: null,
            name: 'Registration timestamp',
            key: 'registration_timestamp',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'datetime',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
        ],
      },
    ],
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
        zgwMocks: [
          mockZGWApisCataloguesGet(),
          mockCaseTypesGet(),
          mockZGWApisDocumenTypesGet(),
          mockZGWApisRoleTypesGet(),
          mockZGWApisProductsGet(),
        ],
        camundaMocks: [mockProcessDefinitionsGet()],
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
          partnersRoltype: '',
          partnersDescription: '',
          childrenRoltype: '',
          childrenDescription: '',
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
          objectsApiGroup: 'objects-group',
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
          variablesMapping: [
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
      {
        key: 'backend7',
        name: 'Failing demo',
        backend: 'failing-demo',
        options: {extraLine: 'Filled out option'},
      },
      {
        key: 'backend8',
        name: 'Crashing demo',
        backend: 'exception-demo',
        options: {extraLine: 'Filled out option'},
      },
      {
        key: 'backend10',
        name: 'Camunda',
        backend: 'camunda',
        options: {
          processDefinition: '',
          processDefinitionVersion: null,
          processVariables: [
            {
              enabled: true,
              componentKey: 'textField1',
              alias: '',
            },
          ],
          complexProcessVariables: [
            {
              enabled: true,
              alias: 'sampleVariable',
              type: 'object',
              definition: {
                foo: {
                  source: 'component',
                  definition: {
                    var: 'textField2',
                  },
                },
              },
            },
          ],
        },
      },
      {
        key: 'backend11',
        name: 'Generic JSON registration',
        backend: 'json_dump',
        options: {
          service: 1,
          path: 'example/endpoint',
          variables: [],
          fixedMetadataVariables: [],
          additionalMetadataVariables: [],
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
          objectsApiGroup: 'objects-group',
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
    expect(modalForm).toHaveFormValues({objectsApiGroup: 'objects-group'});
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
      await rsSelect(catalogueSelect, 'Catalogus 2');
    });

    await step(
      'Path to auth attribute is required if updating existing objects is enabled',
      async () => {
        const otherSettingsTitle = modal.getByRole('heading', {
          name: 'Bestaand object bijwerken (Tonen)',
        });
        expect(otherSettingsTitle).toBeVisible();
        await userEvent.click(within(otherSettingsTitle).getByRole('link', {name: '(Tonen)'}));

        const authAttributePath = modal.getByText('Identificatie-attribuut');

        expect(authAttributePath.parentElement.parentElement).toHaveClass('field--disabled');

        const updateExistingObject = modal.getByLabelText('Bestaand object bijwerken');
        await userEvent.click(updateExistingObject);

        // Checking `updateExistingObject` should make `authAttributePath` no longer disabled
        expect(authAttributePath.parentElement.parentElement).not.toHaveClass('field--disabled');
      }
    );

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

export const ObjectsAPIJsonSchema = {
  args: {
    configuredBackends: [
      {
        key: 'backend4',
        name: 'Objects API',
        backend: 'objects_api',
        options: {
          version: 2,
          objectsApiGroup: 'objects-group',
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
  parameters: {
    msw: {
      handlers: {
        jsonSchemaMocks: [mockFormJsonSchemaGet({type: 'string', title: 'Text field'})],
      },
    },
  },

  play: async ({canvasElement, step, args}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByText('Genereer JSON-schema'));

    const modalForm = await screen.findByRole('dialog');
    expect(modalForm).toBeVisible();
    const modal = within(modalForm);

    expect(
      await modal.getByRole('heading', {name: 'Formulier-JSON-schema: Objects API registration'})
    ).toBeVisible();
    // The json editor can be slow to load, so include a larger timeout to counteract test flakiness
    expect(await modal.findByText(/string/, undefined, {timeout: 5000})).toBeVisible();
    expect(await modal.findByText(/Text field/, undefined, {timeout: 5000})).toBeVisible();
  },
};

export const ObjectsAPIJsonSchemaError = {
  args: {
    configuredBackends: [
      {
        key: 'backend4',
        name: 'Objects API',
        backend: 'objects_api',
        options: {
          version: 2,
          objectsApiGroup: 'objects-group',
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
  parameters: {
    msw: {
      handlers: {
        jsonSchemaMocks: [mockFormJsonSchemaGet()],
      },
    },
  },

  play: async ({canvasElement, step, args}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByText('Genereer JSON-schema'));

    const modalForm = await screen.findByRole('dialog');
    expect(modalForm).toBeVisible();
    const modal = within(modalForm);

    expect(
      await modal.findByText('Er is een fout opgetreden tijdens het genereren van het schema')
    ).toBeVisible();
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
          objectsApiGroup: 'objects-group',
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
    expect(modalForm).toHaveFormValues({objectsApiGroup: 'objects-group'});

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
          partnersRoltype: '',
          partnersDescription: '',
          childrenRoltype: '',
          childrenDescription: '',
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

export const EmailValidationNonFieldErrors = {
  args: {
    configuredBackends: [
      {
        key: 'backend3',
        name: 'Email',
        backend: 'email',
        options: {
          toEmails: ['example@example.nl'],
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
    validationErrors: [
      [
        'form.registrationBackends.0.options.nonFieldErrors',
        'Both email_content_template_html and email_content_template_text are required',
      ],
      ['form.registrationBackends.0.options.email_content_template_text', 'Specific field error'],
    ],
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));

    const modalForm = await screen.findByTestId('modal-form');
    expect(modalForm).toBeVisible();
    const modal = within(modalForm);

    expect(
      modal.getByText(
        'Both email_content_template_html and email_content_template_text are required'
      )
    ).toBeVisible();
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
          variablesMapping: [
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

export const GenericJSON = {
  args: {
    configuredBackends: [
      {
        key: 'backend11',
        name: 'Generic JSON registration',
        backend: 'json_dump',
        options: {
          service: 1,
          path: 'example/endpoint',
          variables: ['firstName', 'lastName', 'foo'],
          fixedMetadataVariables: ['form_name', 'form_version', 'public_reference'],
          additionalMetadataVariables: ['auth_bsn'],
        },
      },
    ],
    availableFormVariables: [
      {
        form: null,
        formDefinition: null,
        name: 'First name',
        key: 'firstName',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: '',
        prefillOptions: {},
        dataType: 'string',
        dataFormat: '',
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: '',
      },
      {
        form: null,
        formDefinition: null,
        name: 'Last name',
        key: 'lastName',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: '',
        prefillOptions: {},
        dataType: 'string',
        dataFormat: '',
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: '',
      },
      {
        form: null,
        formDefinition: null,
        name: 'Attachment',
        key: 'attachment',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: '',
        prefillOptions: {},
        dataType: 'file',
        dataFormat: '',
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: '',
      },
      {
        form: null,
        formDefinition: null,
        name: 'Foo',
        key: 'foo',
        source: 'user_defined',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: '',
        prefillOptions: {},
        dataType: 'string',
        dataFormat: '',
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: 'Bar',
      },
    ],
    availableStaticVariables: [
      {
        form: null,
        formDefinition: null,
        name: 'BSN',
        key: 'auth_bsn',
        source: '',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: '',
        prefillOptions: {},
        dataType: 'string',
        dataFormat: '',
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: '',
      },
      {
        form: null,
        formDefinition: null,
        name: 'Form name',
        key: 'form_name',
        source: '',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: '',
        prefillOptions: {},
        dataType: 'string',
        dataFormat: '',
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: '',
      },
    ],
  },

  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));

    const modalForm = await screen.findByTestId('modal-form');
    expect(modalForm).toBeVisible();
    const modal = within(modalForm);

    await step('Add form variables', async () => {
      expect(...modal.queryAllByText('Attachment')).toBeFalsy(); // Ensure component variable 'Attachment' IS NOT selected
      expect(modal.getByText('Foo')).toBeVisible(); // Ensure user-defined variable 'Foo' IS selected

      await userEvent.click(
        modal.getByRole('button', {name: 'Alle formuliervariabelen toevoegen'})
      );
      expect(modal.getByText('Attachment')).toBeVisible(); // Ensure 'Attachment' IS selected
      expect(modal.getByText('Foo')).toBeVisible(); // Ensure user-defined variable 'Foo' IS STILL selected

      // Close modal
      await userEvent.click(modal.getByRole('button', {name: 'Opslaan'}));
    });

    // Re-open modal for visual regression testing
    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));
  },
};
