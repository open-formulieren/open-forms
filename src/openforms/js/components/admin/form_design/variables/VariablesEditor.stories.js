import {expect, fn, screen, userEvent, waitFor, within} from '@storybook/test';
import selectEvent from 'react-select-event';

import {
  mockObjectsAPIPrefillPropertiesGet,
  mockPrefillAttributesGet,
} from 'components/admin/form_design/mocks';
import {BACKEND_OPTIONS_FORMS} from 'components/admin/form_design/registrations';
import {mockTargetPathsPost} from 'components/admin/form_design/registrations/objectsapi/mocks';

import {serializeValue} from '../../forms/VariableMapping';
import {mockObjecttypeVersionsGet, mockObjecttypesGet} from '../registrations/objectsapi/mocks';
import {FormDecorator, withReactSelectDecorator} from '../story-decorators';
import VariablesEditor from './VariablesEditor';

BACKEND_OPTIONS_FORMS.testPlugin = {
  configurableFromVariables: true,
  summaryHandler: () => 'placeholder',
  variableConfigurationEditor: () => 'placeholder',
};

const VARIABLES = [
  {
    form: 'http://localhost:8000/api/v2/forms/36612390',
    formDefinition: 'http://localhost:8000/api/v2/form-definitions/6de1ea5a',
    name: 'Form.io component',
    key: 'formioComponent',
    source: 'component',
    prefillPlugin: '',
    prefillAttribute: '',
    prefillIdentifierRole: 'main',
    dataType: 'string',
    dataFormat: undefined,
    isSensitiveData: false,
    serviceFetchConfiguration: undefined,
    initialValue: '',
  },
  {
    form: 'http://localhost:8000/api/v2/forms/36612390',
    formDefinition: 'http://localhost:8000/api/v2/form-definitions/6de1ea5a',
    name: 'Single File',
    key: 'aSingleFile',
    source: 'component',
    prefillPlugin: '',
    prefillAttribute: '',
    prefillIdentifierRole: 'main',
    dataType: 'array',
    dataFormat: undefined,
    isSensitiveData: false,
    serviceFetchConfiguration: undefined,
    initialValue: [],
  },
  {
    form: 'http://localhost:8000/api/v2/forms/36612390',
    formDefinition: 'http://localhost:8000/api/v2/form-definitions/6de1ea5a',
    name: 'Multiple File',
    key: 'aMultipleFile',
    source: 'component',
    prefillPlugin: '',
    prefillAttribute: '',
    prefillIdentifierRole: 'main',
    dataType: 'array',
    dataFormat: undefined,
    isSensitiveData: false,
    serviceFetchConfiguration: undefined,
    initialValue: [],
  },
  {
    form: 'http://localhost:8000/api/v2/forms/36612390',
    formDefinition: undefined,
    name: 'User defined',
    key: 'userDefined',
    source: 'user_defined',
    prefillPlugin: 'objects_api',
    prefillAttribute: '',
    prefillIdentifierRole: 'main',
    dataType: 'array',
    dataFormat: undefined,
    isSensitiveData: false,
    serviceFetchConfiguration: undefined,
    initialValue: [],
    prefillOptions: {
      objectsApiGroup: 1,
      objecttypeUuid: '2c77babf-a967-4057-9969-0200320d23f2',
      objecttypeVersion: 1,
      variablesMapping: [{variableKey: 'formioComponent', targetPath: ['firstName']}],
    },
  },
];

export default {
  title: 'Form design / Variables editor',
  component: VariablesEditor,
  decorators: [FormDecorator],
  args: {
    variables: VARIABLES,
    availableFormVariables: VARIABLES,
    availableStaticVariables: [
      {
        form: null,
        formDefinition: null,
        name: 'Now',
        key: 'now',
        source: '',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataType: 'datetime',
        dataFormat: '',
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: '2024-02-27T16:44:22.170405Z',
      },
    ],
    availableComponents: {
      aSingleFile: {
        type: 'file',
        multiple: false,
        key: 'aSingleFile',
      },
      aMultipleFile: {
        type: 'file',
        multiple: true,
        key: 'aMultipleFile',
      },
      formioComponent: {
        key: 'formioComponent',
        type: 'textfield',
      },
    },
    availablePrefillPlugins: [
      {id: 'stuf-bg', label: 'StUF-BG'},
      {id: 'haalcentraal', label: 'BRP Personen (HaalCentraal)'},
      {
        id: 'objects_api',
        label: 'Objects API',
        configurationContext: {
          apiGroups: [
            [1, 'Objects API group 1'],
            [2, 'Objects API group 2'],
          ],
        },
      },
    ],
    onChange: fn(),
    onAdd: fn(),
    onDelete: fn(),
    onFieldChange: fn(),
  },
  parameters: {
    msw: {
      handlers: {
        prefill: [
          mockPrefillAttributesGet({
            'stuf-bg': [
              {id: 'bsn', label: 'BSN'},
              {id: 'postcode', label: 'Postcode'},
            ],
            haalcentraal: [
              {id: 'bsn', label: 'BSN'},
              {id: 'verblijfsAdres.postcode', label: 'Verblijfsadres > Postcode'},
            ],
            objects_api: [
              {id: 'street', label: 'Address > street'},
              {id: 'firstName', label: 'First name'},
              {id: 'lastName', label: 'Last name'},
              {id: 'age', label: 'Age'},
            ],
          }),
          mockObjectsAPIPrefillPropertiesGet({
            '2c77babf-a967-4057-9969-0200320d23f2': {
              1: [
                {
                  targetPath: ['firstName'],
                  jsonSchema: {type: 'string', description: 'First name'},
                },
                {
                  targetPath: ['lastName'],
                  jsonSchema: {type: 'string', description: 'Last name'},
                },
                {targetPath: ['age'], jsonSchema: {type: 'integer', description: 'Age'}},
              ],
            },
            '2c77babf-a967-4057-9969-0200320d23f1': {
              1: [{targetPath: ['height'], jsonSchema: {type: 'integer', description: 'Height'}}],
              2: [
                {targetPath: ['height'], jsonSchema: {type: 'integer', description: 'Height'}},
                {targetPath: ['species'], jsonSchema: {type: 'string', description: 'Species'}},
              ],
            },
          }),
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
  },
};

export const Default = {};

export const WithObjectsAPIRegistrationBackends = {
  args: {
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 1,
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          variablesMapping: [
            {
              variableKey: 'formioComponent',
              targetPath: ['path', 'to.the', 'target'],
            },
            {
              variableKey: 'userDefined',
              targetPath: ['other', 'path'],
            },
          ],
        },
      },
      {
        backend: 'objects_api',
        key: 'objects_api_2',
        name: 'Other Objects API registration with a long name',
        options: {
          version: 2,
          objectsApiGroup: 1,
          objecttype: '209e0341-834d-4060-bd19-a3419d19ed74',
          objecttypeVersion: 2,
          variablesMapping: [
            {
              variableKey: 'formioComponent',
              targetPath: ['path', 'to.the', 'target'],
            },
          ],
        },
      },
      {
        backend: 'objects_api',
        key: 'objects_api_3',
        name: "Shouldn't display!",
        options: {
          version: 1,
          objectsApiGroup: 1,
          objecttype: '209e0341-834d-4060-bd19-a3419d19ed74',
          objecttypeVersion: 2,
        },
      },
    ],
    registrationPluginsVariables: [
      {
        pluginIdentifier: 'objects_api',
        pluginVerboseName: 'Objects API registration',
        pluginVariables: [
          {
            form: null,
            formDefinition: null,
            name: 'PDF Url',
            key: 'pdf_url',
            source: '',
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            dataType: 'string',
            dataFormat: '',
            isSensitiveData: false,
            serviceFetchConfiguration: undefined,
            initialValue: '',
          },
        ],
      },
      {
        pluginIdentifier: 'zgw-create-zaak',
        pluginVerboseName: "ZGW API's",
        pluginVariables: [
          {
            form: null,
            formDefinition: null,
            name: 'ZGW specific variable',
            key: 'zgw_var',
            source: '',
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            dataType: 'string',
            dataFormat: '',
            isSensitiveData: false,
            serviceFetchConfiguration: undefined,
            initialValue: '',
          },
        ],
      },
    ],
    onFieldChange: data => {
      console.log(data);
    },
  },
  parameters: {
    msw: {
      handlers: [
        mockTargetPathsPost({
          string: [
            {
              targetPath: ['path', 'to.the', 'target'],
              isRequired: true,
              jsonSchema: {type: 'string'},
            },
          ],
          object: [
            {
              targetPath: ['other', 'path'],
              isRequired: false,
              jsonSchema: {type: 'object', properties: {a: {type: 'string'}}, required: ['a']},
            },
          ],
        }),
      ],
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const registrationTab = canvas.getByRole('tab', {name: 'Registratie'});
    await userEvent.click(registrationTab);

    const pdfUrl = canvas.getByRole('cell', {name: 'pdf_url'});
    expect(pdfUrl).toBeVisible();

    // With a single backend, the heading shouldn't display:
    const objectsApiTitle = canvas.queryByRole('heading', {name: 'Objects API registration'});
    expect(objectsApiTitle).toBeNull();
  },
};

export const FilesMappingAndObjectAPIRegistration = {
  args: {
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 1,
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          variablesMapping: [
            {
              variableKey: 'formioComponent',
              targetPath: ['path', 'to.the', 'target'],
            },
            {
              variableKey: 'userDefined',
              targetPath: ['other', 'path'],
            },
          ],
        },
      },
    ],
    registrationPluginsVariables: [
      {
        pluginIdentifier: 'objects_api',
        pluginVerboseName: 'Objects API registration',
      },
    ],
    onFieldChange: data => {
      console.log(data);
    },
  },
  parameters: {
    msw: {
      handlers: [
        mockTargetPathsPost({
          string: [
            {
              targetPath: ['path', 'to.the', 'target'],
              isRequired: true,
              jsonSchema: {type: 'string'},
            },
            {
              targetPath: ['path', 'to', 'uri'],
              isRequired: true,
              jsonSchema: {
                type: 'string',
                format: 'uri',
              },
            },
          ],
          object: [
            {
              targetPath: ['other', 'path'],
              isRequired: false,
              jsonSchema: {type: 'object', properties: {a: {type: 'string'}}, required: ['a']},
            },
          ],
          array: [
            {
              targetPath: ['path', 'to', 'array'],
              isRequired: true,
              jsonSchema: {type: 'array'},
            },
          ],
        }),
      ],
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const editIcons = canvas.getAllByTitle('Registratie-instellingen bewerken');

    // The second icon is for the single file upload component variable
    userEvent.click(editIcons[1]);

    const targetSchemaDropdown = await screen.findByRole('combobox');

    await expect(targetSchemaDropdown).toBeInTheDocument();

    // Only the targets of type string should appear
    await expect(
      await screen.findByRole('option', {name: 'path > to.the > target (verplicht)'})
    ).toBeVisible();
    await expect(
      await screen.findByRole('option', {name: 'path > to > uri (verplicht)'})
    ).toBeVisible();

    const saveButton = screen.getByRole('button', {name: 'Opslaan'});
    userEvent.click(saveButton);

    // The third icon is for the multiple file upload component variable
    userEvent.click(editIcons[2]);

    const dropdown = await screen.findByRole('combobox');

    await expect(dropdown).toBeInTheDocument();
    await expect(
      await screen.findByRole('option', {name: 'path > to > array (verplicht)'})
    ).toBeVisible();
  },
};

export const WithObjectsAPIAndTestRegistrationBackends = {
  args: {
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 1,
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          variablesMapping: [
            {
              variableKey: 'formioComponent',
              targetPath: ['path', 'to.the', 'target'],
            },
            {
              variableKey: 'userDefined',
              targetPath: ['other', 'path'],
            },
          ],
        },
      },
      {
        backend: 'testPlugin',
        key: 'test_backend',
        name: 'Example test registration',
        options: {},
      },
      {
        backend: 'stuf-zds-create-zaak',
        key: 'test_zds',
        name: 'Example ZDS registration',
        options: {},
      },
    ],
    registrationPluginsVariables: [
      {
        pluginIdentifier: 'objects_api',
        pluginVerboseName: 'Objects API registration',
        pluginVariables: [
          {
            form: null,
            formDefinition: null,
            name: 'PDF Url',
            key: 'pdf_url',
            source: '',
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            dataType: 'string',
            dataFormat: '',
            isSensitiveData: false,
            serviceFetchConfiguration: undefined,
            initialValue: '',
          },
        ],
      },
      {
        pluginIdentifier: 'testPlugin',
        pluginVerboseName: 'Test plugin',
        pluginVariables: [
          {
            form: null,
            formDefinition: null,
            name: 'Test plugin variable',
            key: 'test_plugin_var',
            source: '',
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            dataType: 'string',
            dataFormat: '',
            isSensitiveData: false,
            serviceFetchConfiguration: undefined,
            initialValue: '',
          },
        ],
      },
    ],
    onFieldChange: data => {
      console.log(data);
    },
  },
  parameters: {
    msw: {
      handlers: [
        mockTargetPathsPost({
          string: [
            {
              targetPath: ['path', 'to.the', 'target'],
              isRequired: true,
              jsonSchema: {type: 'string'},
            },
          ],
          object: [
            {
              targetPath: ['other', 'path'],
              isRequired: false,
              jsonSchema: {type: 'object', properties: {a: {type: 'string'}}, required: ['a']},
            },
          ],
        }),
      ],
    },
  },
};

export const ConfigurePrefill = {
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const userDefinedVarsTab = await canvas.findByRole('tab', {name: 'Gebruikersvariabelen'});
    expect(userDefinedVarsTab).toBeVisible();
    await userEvent.click(userDefinedVarsTab);

    // open modal for configuration
    const editIcon = canvas.getByTitle('Prefill instellen');
    await userEvent.click(editIcon);

    const pluginDropdown = await screen.findByLabelText('Plugin');
    expect(pluginDropdown).toBeVisible();
    expect(await within(pluginDropdown).findByRole('option', {name: 'StUF-BG'})).toBeVisible();
  },
};

export const ConfigurePrefillObjectsAPI = {
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await step('Open configuration modal', async () => {
      const userDefinedVarsTab = await canvas.findByRole('tab', {name: 'Gebruikersvariabelen'});
      expect(userDefinedVarsTab).toBeVisible();
      await userEvent.click(userDefinedVarsTab);

      // open modal for configuration
      const editIcon = canvas.getByTitle('Prefill instellen');
      await userEvent.click(editIcon);
      expect(await canvas.findByRole('dialog')).toBeVisible();
    });

    await step('Configure Objects API prefill', async () => {
      const modal = within(await canvas.findByRole('dialog'));
      const pluginDropdown = await screen.findByLabelText('Plugin');
      expect(pluginDropdown).toBeVisible();
      await userEvent.selectOptions(pluginDropdown, 'Objects API');

      // check mappings
      const variableSelect = await screen.findByLabelText('Formuliervariabele');
      expect(variableSelect).toBeVisible();
      expect(modal.getByText('Form.io component')).toBeVisible();

      // Wait until the API call to retrieve the prefillAttributes is done
      await waitFor(async () => {
        const prefillPropertySelect = await screen.findByLabelText(
          'Selecteer een attribuut uit het objecttype'
        );
        expect(prefillPropertySelect).toBeVisible();
        expect(prefillPropertySelect).toHaveValue(serializeValue(['firstName']));
      });
    });
  },
};

export const ConfigurePrefillObjectsAPIWithCopyButton = {
  // decorators: [FormDecorator, withReactSelectDecorator],
  args: {
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 1,
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          variablesMapping: [
            {
              variableKey: 'formioComponent',
              targetPath: ['height'],
            },
            {
              variableKey: 'userDefined',
              targetPath: ['species'],
            },
          ],
        },
      },
      {
        backend: 'objects_api',
        key: 'objects_api_2',
        name: 'Other Objects API registration with a long name',
        options: {
          version: 2,
          objectsApiGroup: 1,
          objecttype: '209e0341-834d-4060-bd19-a3419d19ed74',
          objecttypeVersion: 2,
          variablesMapping: [
            {
              variableKey: 'formioComponent',
              targetPath: ['path', 'to.the', 'target'],
            },
          ],
        },
      },
    ],
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await step('Open configuration modal', async () => {
      const userDefinedVarsTab = await canvas.findByRole('tab', {name: 'Gebruikersvariabelen'});
      expect(userDefinedVarsTab).toBeVisible();
      await userEvent.click(userDefinedVarsTab);

      // open modal for configuration
      const editIcon = canvas.getByTitle('Prefill instellen');
      await userEvent.click(editIcon);
      expect(await screen.findByRole('dialog')).toBeVisible();
    });

    await step('Configure Objects API prefill with copy button', async () => {
      const modal = within(await screen.findByRole('dialog'));
      const pluginDropdown = await screen.findByLabelText('Plugin');
      expect(pluginDropdown).toBeVisible();
      await userEvent.selectOptions(pluginDropdown, 'Objects API');

      const copyDropdown = await modal.findByLabelText(
        'Copy configuration from registration backend'
      );
      expect(copyDropdown).toBeVisible();
      await userEvent.click(copyDropdown);

      // Cannot do selectOption with react-select
      const options = await canvas.findAllByText('Example Objects API reg.');
      const option = options[1];
      console.log(option);
      await userEvent.click(option);

      const copyButton = await canvas.findByRole('button', {
        name: 'Copy',
      });
      expect(copyButton).toBeVisible();
      await userEvent.click(copyButton);

      // Click the confirmation button
      const button = canvas.getByRole('button', {
        name: 'Accepteren',
      });
      expect(button).toBeVisible();
      await userEvent.click(button);

      const modalForm = await screen.findByTestId('modal-form');
      expect(modalForm).toBeVisible();
      const propertyDropdowns = await modal.findAllByLabelText(
        'Selecteer een attribuut uit het objecttype'
      );

      // Wait until the API call to retrieve the prefillAttributes is done
      await waitFor(
        async () => {
          expect(modalForm).toHaveFormValues({
            'options.objectsApiGroup': '1',
            'options.objecttypeUuid': '2c77babf-a967-4057-9969-0200320d23f1',
            'options.objecttypeVersion': '2',
          });

          expect(propertyDropdowns[0]).toHaveValue(serializeValue(['height']));
          expect(propertyDropdowns[1]).toHaveValue(serializeValue(['species']));
        },
        {timeout: 2000}
      );
    });
  },
};

export const WithValidationErrors = {
  args: {
    variables: [
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: 'http://localhost:8000/api/v2/form-definitions/6de1ea5a',
        name: 'Form.io component',
        key: 'formioComponent',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataType: 'string',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: '',
      },
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: undefined,
        name: 'User defined',
        key: 'userDefined',
        source: 'user_defined',
        prefillPlugin: 'bad-plugin',
        prefillAttribute: 'bad-attribute',
        prefillIdentifierRole: 'invalid',
        dataType: 'array',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
        errors: {
          name: ['A validation error for the name.'],
          key: 'The key must be unique.',
          prefillPlugin: ['Invalid plugin selected.'],
          prefillAttribute: ['Invalid attribute selected.'],
          prefillIdentifierRole: ['Invalid identifier role.'],
        },
      },
    ],
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const userDefinedVarsTab = await canvas.findByRole('tab', {name: 'Gebruikersvariabelen'});
    expect(userDefinedVarsTab).toBeVisible();
    await userEvent.click(userDefinedVarsTab);

    // open modal for configuration
    const editIcon = canvas.getByTitle('Prefill instellen');
    await userEvent.click(editIcon);
  },
};
