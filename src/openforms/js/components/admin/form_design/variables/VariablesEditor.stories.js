import {expect, screen, userEvent, within} from '@storybook/test';

import {BACKEND_OPTIONS_FORMS} from 'components/admin/form_design/registrations';
import {mockTargetPathsPost} from 'components/admin/form_design/registrations/objectsapi/mocks';

import {FormDecorator} from '../story-decorators';
import VariablesEditor from './VariablesEditor';

BACKEND_OPTIONS_FORMS.testPlugin = {
  configurableFromVariables: true,
  summaryHandler: () => 'placeholder',
  variableConfigurationEditor: () => 'placeholder',
};

export default {
  title: 'Form design / Variables editor',
  component: VariablesEditor,
  decorators: [FormDecorator],
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
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataType: 'array',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
      },
    ],
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
  },
  argTypes: {
    onChange: {action: true},
    onAdd: {action: true},
    onDelete: {action: true},
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
