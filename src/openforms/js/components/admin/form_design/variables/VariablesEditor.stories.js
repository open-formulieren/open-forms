import {expect, fn, userEvent, waitFor, within} from '@storybook/test';
import selectEvent from 'react-select-event';

import {
  mockObjectsAPIPrefillPropertiesGet,
  mockPrefillAttributesGet,
} from 'components/admin/form_design/mocks';
import {BACKEND_OPTIONS_FORMS} from 'components/admin/form_design/registrations';
import {mockTargetPathsPost} from 'components/admin/form_design/registrations/objectsapi/mocks';
import {
  mockObjecttypeVersionsGet,
  mockObjecttypesGet,
} from 'components/admin/form_design/registrations/objectsapi/mocks';
import {FormDecorator} from 'components/admin/form_design/story-decorators';
import {serializeValue} from 'components/admin/forms/VariableMapping';
import {findReactSelectMenu, rsSelect} from 'utils/storybookTestHelpers';

import VariablesEditor from './VariablesEditor';

BACKEND_OPTIONS_FORMS.testPlugin = {
  configurableFromVariables: true,
  summaryHandler: () => 'placeholder',
  variableConfigurationEditor: () => 'placeholder',
};

const AVAILABLE_FORM_STEPS = [
  {
    formDefinition: 'http://localhost:8000/api/v2/form-definitions/6de1ea5a',
    configuration: {display: 'form', components: []},
    slug: 'step-1',
    name: 'Step 1',
    url: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5/steps/8f046d57-ef41-41e0-bb7a-a8dc618b9d43',
    uuid: '8f046d57-ef41-41e0-bb7a-a8dc618b9d43',
    _generatedId: '',
    isNew: false,
    validationErrors: [],
  },
  {
    formDefinition: '',
    configuration: {display: 'form', components: []},
    slug: 'step-2',
    name: 'Step 2',
    url: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5/steps/fe599c97',
    uuid: 'fe599c97',
    _generatedId: 'unsaved-step',
    isNew: true,
    validationErrors: [],
  },
];

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
    formDefinition: 'unsaved-step',
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
      objectsApiGroup: 'group-1',
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
    availableFormSteps: AVAILABLE_FORM_STEPS,
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
      {
        id: 'stuf-bg',
        label: 'StUF-BG',
        requiresAuth: ['bsn'],
        requiresAuthPlugin: [],
      },
      {
        id: 'haalcentraal',
        label: 'BRP Personen (HaalCentraal)',
        requiresAuth: ['bsn'],
        requiresAuthPlugin: [],
      },
      {
        id: 'objects_api',
        label: 'Objects API',
        configurationContext: {
          apiGroups: [
            ['group-1', 'Objects API group 1'],
            ['group-2', 'Objects API group 2'],
          ],
        },
        requiresAuth: [],
        requiresAuthPlugin: [],
      },
      {
        id: 'family_members',
        label: 'Family members',
        requiresAuth: ['bsn'],
        requiresAuthPlugin: [],
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
            '209e0341-834d-4060-bd19-a3419d19ed74': {
              1: [
                {
                  targetPath: ['path', 'to.the', 'target'],
                  jsonSchema: {type: 'string', description: 'Path to the target'},
                },
              ],
              2: [
                {
                  targetPath: ['path', 'to.the', 'target'],
                  jsonSchema: {type: 'string', description: 'Path to the target'},
                },
              ],
            },
          }),
        ],
        objectsAPIPrefill: [
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
            {
              url: 'https://objecttypen.nl/api/v1/objecttypes/209e0341-834d-4060-bd19-a3419d19ed74',
              uuid: '209e0341-834d-4060-bd19-a3419d19ed74',
              name: 'Other objecttype',
              namePlural: 'Other objecttypes',
              dataClassification: 'open',
            },
          ]),
          mockObjecttypeVersionsGet([
            {version: 1, status: 'published'},
            {version: 2, status: 'draft'},
          ]),
        ],
        objectTypeTargetPaths: [
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
          objectsApiGroup: 'group-1',
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
          geometryVariableKey: '',
        },
      },
      {
        backend: 'objects_api',
        key: 'objects_api_2',
        name: 'Other Objects API registration with a long name',
        options: {
          version: 2,
          objectsApiGroup: 'group-1',
          objecttype: '209e0341-834d-4060-bd19-a3419d19ed74',
          objecttypeVersion: 2,
          variablesMapping: [
            {
              variableKey: 'formioComponent',
              targetPath: ['path', 'to.the', 'target'],
            },
          ],
          geometryVariableKey: '',
        },
      },
      {
        backend: 'objects_api',
        key: 'objects_api_3',
        name: "Shouldn't display!",
        options: {
          version: 1,
          objectsApiGroup: 'group-1',
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
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const registrationTab = canvas.getByRole('tab', {name: 'Registratie'});
    await userEvent.click(registrationTab);

    const pdfUrl = canvas.getByRole('cell', {name: 'pdf_url'});
    expect(pdfUrl).toBeVisible();

    // With all backends of the same type, the heading shouldn't display
    const objectsApiTitle = canvas.queryByRole('heading', {name: 'Objects API registration'});
    expect(objectsApiTitle).toBeNull();
  },
};

export const WithObjectsAPIRegistrationBackendsTransformToList = {
  args: {
    availableFormVariables: [
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
        formDefinition: 'unsaved-step',
        name: 'Select boxes list',
        key: 'selectBoxesList',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
      },
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: 'unsaved-step',
        name: 'Select boxes object',
        key: 'selectBoxesObj',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
      },
    ],
    availableComponents: {
      formioComponent: {
        key: 'formioComponent',
        type: 'textfield',
      },
      selectBoxesList: {
        type: 'selectboxes',
        multiple: false,
        key: 'selectBoxesList',
      },
      selectBoxesObj: {
        type: 'selectboxes',
        multiple: false,
        key: 'selectBoxesObj',
      },
    },
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 'group-1',
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          variablesMapping: [],
          transformToList: ['selectBoxesList'],
        },
      },
    ],
  },
  parameters: {
    msw: {
      handlers: {
        objectTypeTargetPaths: [
          mockTargetPathsPost({
            object: [
              {
                targetPath: ['path', 'to.the', 'target'],
                isRequired: false,
                jsonSchema: {type: 'object'},
              },
            ],
            array: [
              {
                targetPath: ['other', 'path'],
                isRequired: false,
                jsonSchema: {type: 'array'},
              },
            ],
            string: [
              {
                targetPath: ['path'],
                isRequired: false,
                jsonSchema: {type: 'string'},
              },
            ],
          }),
        ],
      },
    },
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);
    const editIcons = canvas.getAllByTitle('Registratie-instellingen bewerken');

    expect(editIcons).toHaveLength(3);

    await step('Simple component', async () => {
      await userEvent.click(editIcons[0]);

      const transformToListCheckbox = canvas.queryByLabelText('Verstuur als lijst');
      expect(transformToListCheckbox).toBeNull();

      const saveButton = canvas.getByRole('button', {name: 'Opslaan'});
      await userEvent.click(saveButton);
    });

    await step('Select boxes with transform to list', async () => {
      await userEvent.click(editIcons[1]);

      const transformToListCheckbox = await canvas.findByLabelText('Verstuur als lijst');
      expect(transformToListCheckbox).toBeChecked();

      const saveButton = canvas.getByRole('button', {name: 'Opslaan'});
      await userEvent.click(saveButton);
    });

    await step('Select boxes without transform to list (default behaviour -> object)', async () => {
      await userEvent.click(editIcons[2]);

      const transformToListCheckbox = await canvas.findByLabelText('Verstuur als lijst');
      expect(transformToListCheckbox).not.toBeChecked();

      const saveButton = canvas.getByRole('button', {name: 'Opslaan'});
      await userEvent.click(saveButton);
    });
  },
};

export const WithObjectsAPIRegistrationBackendsGeometryField = {
  args: {
    availableFormVariables: [
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: 'unsaved-step',
        name: 'Map object',
        key: 'map',
        type: 'map',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
      },
    ],
    availableComponents: {
      map: {
        type: 'map',
        multiple: false,
        key: 'map',
      },
    },
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 'group-1',
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          variablesMapping: [],
          transformToList: [],
          geometryvariableKey: '',
        },
      },
    ],
  },
  parameters: {
    msw: {
      handlers: {
        objectTypeTargetPaths: [
          mockTargetPathsPost({
            object: [
              {
                targetPath: ['path', 'to.the', 'target'],
                isRequired: false,
                jsonSchema: {type: 'object'},
              },
            ],
          }),
        ],
      },
    },
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);
    const editIcons = canvas.getAllByTitle('Registratie-instellingen bewerken');

    expect(editIcons).toHaveLength(1);

    await userEvent.click(editIcons[0]);

    const geometryCheckbox = canvas.queryByLabelText('Koppel aan geometrie-veld');
    const targetPathSelect = await canvas.findByLabelText('Bestemmingspad');

    expect(geometryCheckbox).not.toBeChecked();
    expect(targetPathSelect).not.toBeDisabled();

    await userEvent.click(geometryCheckbox);

    expect(targetPathSelect).toBeDisabled();
  },
};

// gh-4978 regression for geometry field on empty variable
export const EmptyUserDefinedVariableWithObjectsAPIRegistration = {
  args: {
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 'group-1',
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
          geometryVariableKey: '',
        },
      },
    ],
    availableFormVariables: [
      // add a variable as if the user clicked "add new user defined variable"
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: undefined,
        name: '',
        key: '',
        source: 'user_defined',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataType: 'string',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: '',
        prefillOptions: {},
      },
    ],
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const userDefinedVarsTab = canvas.getByRole('tab', {name: /Gebruikersvariabelen/});
    await userEvent.click(userDefinedVarsTab);
    expect(canvas.queryAllByText('record.geometry')).toHaveLength(0);
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
          objectsApiGroup: 'group-1',
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
    ],
  },
  parameters: {
    msw: {
      handlers: {
        objectTypeTargetPaths: [
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
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    const editIcons = canvas.getAllByTitle('Registratie-instellingen bewerken');
    expect(editIcons).toHaveLength(3);

    await step('Single file component', async () => {
      // The second icon is for the single file upload component variable
      await userEvent.click(editIcons[1]);

      const targetSchemaDropdown = await canvas.findByRole('combobox', {name: 'Bestemmingspad'});
      expect(targetSchemaDropdown).toBeVisible();
      selectEvent.openMenu(targetSchemaDropdown);

      // Only the targets of type string should appear
      const targetSelectMenu = within(await findReactSelectMenu(canvas));
      expect(
        await targetSelectMenu.findByRole('option', {name: 'path > to.the > target (verplicht)'})
      ).toBeVisible();
      expect(
        await targetSelectMenu.findByRole('option', {name: 'path > to > uri (verplicht)'})
      ).toBeVisible();

      const saveButton = canvas.getByRole('button', {name: 'Opslaan'});
      userEvent.click(saveButton);
    });

    await step('Multi file component', async () => {
      // The third icon is for the multiple file upload component variable
      await userEvent.click(editIcons[2]);

      const targetSchemaDropdown = await canvas.findByRole('combobox', {name: 'Bestemmingspad'});
      expect(targetSchemaDropdown).toBeVisible();
      selectEvent.openMenu(targetSchemaDropdown);

      // Only the targets of type array should appear
      const targetSelectMenu = within(await findReactSelectMenu(canvas));
      expect(
        await targetSelectMenu.findByRole('option', {name: 'path > to > array (verplicht)'})
      ).toBeVisible();
    });
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
          objectsApiGroup: 'group-1',
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

    // With multiple backends configured, and two of them introduce registration variables,
    // the plugin headings should be visible.
    expect(canvas.getByRole('heading', {name: 'Objects API registration'})).toBeVisible();
    expect(canvas.getByRole('heading', {name: 'Test plugin'})).toBeVisible();

    // Navigate back to component tab for visual regression testing
    const componentTab = canvas.getByRole('tab', {name: /Component/});
    await componentTab.click(componentTab);
  },
};

export const WithGenericJSONRegistrationBackend = {
  args: {
    registrationBackends: [
      {
        backend: 'json_dump',
        key: 'test_json_dump_backend',
        name: 'Generic JSON registration',
        options: {
          service: 2,
          path: 'test',
          variables: ['aSingleFile'],
          fixedMetadataVariables: ['public_reference'],
          additionalMetadataVariables: ['now'],
        },
      },
    ],
    registrationPluginsVariables: [
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
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    const editIcons = canvas.getAllByTitle('Registratie-instellingen bewerken');
    expect(editIcons).toHaveLength(3);

    await step('formioComponent checkboxes unchecked', async () => {
      await userEvent.click(editIcons[0]);

      const checkboxes = await canvas.getAllByRole('checkbox');
      expect(checkboxes[0]).not.toBeChecked();
      expect(checkboxes[1]).not.toBeChecked();
      expect(checkboxes[1]).toBeDisabled();

      const saveButton = canvas.getByRole('button', {name: 'Opslaan'});
      await userEvent.click(saveButton);
    });

    await step('aSingleFile values checkbox checked and metadata checkbox unchecked', async () => {
      await userEvent.click(editIcons[1]);

      const checkboxes = await canvas.findAllByRole('checkbox');
      expect(checkboxes[0]).toBeChecked();
      expect(checkboxes[1]).not.toBeChecked();

      const saveButton = canvas.getByRole('button', {name: 'Opslaan'});
      await userEvent.click(saveButton);
    });

    await step('now values checkbox unchecked and metadata checkbox checked', async () => {
      const staticVariables = canvas.getByRole('tab', {name: /Vaste variabelen/});
      await userEvent.click(staticVariables);

      const editIcon = canvas.getByTitle('Registratie-instellingen bewerken');
      await userEvent.click(editIcon);

      const checkboxes = await canvas.findAllByRole('checkbox');
      expect(checkboxes[0]).not.toBeChecked();
      expect(checkboxes[1]).toBeChecked();
      expect(checkboxes[1]).not.toBeDisabled();
    });

    await step(
      'public_registration values checkbox unchecked and metadata checkbox checked',
      async () => {
        const registrationVariables = canvas.getByRole('tab', {name: /Registratie/});
        await userEvent.click(registrationVariables);

        const editIcon = canvas.getByTitle('Registratie-instellingen bewerken');
        await userEvent.click(editIcon);

        const checkboxes = await canvas.findAllByRole('checkbox');
        expect(checkboxes[0]).not.toBeChecked();
        expect(checkboxes[1]).toBeChecked();
        expect(checkboxes[1]).toBeDisabled();
      }
    );
  },
};

export const WithGenericJSONRegistrationBackendTransformToList = {
  args: {
    availableFormVariables: [
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
        formDefinition: 'unsaved-step',
        name: 'Select boxes list',
        key: 'selectBoxesList',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
      },
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: 'unsaved-step',
        name: 'Select boxes object',
        key: 'selectBoxesObj',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
      },
    ],
    availableComponents: {
      formioComponent: {
        key: 'formioComponent',
        type: 'textfield',
      },
      selectBoxesList: {
        type: 'selectboxes',
        multiple: false,
        key: 'selectBoxesList',
      },
      selectBoxesObj: {
        type: 'selectboxes',
        multiple: false,
        key: 'selectBoxesObj',
      },
    },
    registrationBackends: [
      {
        backend: 'json_dump',
        key: 'test_json_dump_backend',
        name: 'Generic JSON registration',
        options: {
          service: 2,
          path: 'test',
          variables: ['formioComponent', 'selectBoxesList', 'selectBoxesObj'],
          fixedMetadataVariables: ['public_reference'],
          additionalMetadataVariables: ['now'],
          transformToList: ['selectBoxesList'],
        },
      },
    ],
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);
    const editIcons = canvas.getAllByTitle('Registratie-instellingen bewerken');

    expect(editIcons).toHaveLength(3);

    await step('Simple component', async () => {
      await userEvent.click(editIcons[0]);

      const checkboxes = await canvas.findAllByRole('checkbox');
      expect(checkboxes).toHaveLength(2);

      expect(checkboxes[0]).toBeChecked();
      expect(checkboxes[1]).toBeDisabled();

      const saveButton = canvas.getByRole('button', {name: 'Opslaan'});
      await userEvent.click(saveButton);
    });

    await step('Select boxes with transform to list', async () => {
      await userEvent.click(editIcons[1]);

      const checkboxes = await canvas.findAllByRole('checkbox');
      expect(checkboxes).toHaveLength(3);

      expect(checkboxes[0]).toBeChecked();
      expect(checkboxes[1]).not.toBeChecked();
      expect(checkboxes[2]).toBeChecked();

      const saveButton = canvas.getByRole('button', {name: 'Opslaan'});
      await userEvent.click(saveButton);
    });

    await step('Select boxes without transform to list (default behaviour -> object)', async () => {
      await userEvent.click(editIcons[2]);

      const checkboxes = await canvas.findAllByRole('checkbox');
      expect(checkboxes).toHaveLength(3);
      expect(checkboxes[0]).toBeChecked();
      expect(checkboxes[1]).not.toBeChecked();
      expect(checkboxes[2]).not.toBeChecked();

      const saveButton = canvas.getByRole('button', {name: 'Opslaan'});
      await userEvent.click(saveButton);
    });
  },
};

export const ConfigurePrefill = {
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const userDefinedVarsTab = await canvas.findByRole('tab', {name: /Gebruikersvariabelen/});
    expect(userDefinedVarsTab).toBeVisible();
    await userEvent.click(userDefinedVarsTab);

    // open modal for configuration
    const editIcon = canvas.getByTitle('Prefill instellen');
    await userEvent.click(editIcon);

    const pluginDropdown = await canvas.findByLabelText('Plugin');
    expect(pluginDropdown).toBeVisible();
    expect(await within(pluginDropdown).findByRole('option', {name: 'StUF-BG'})).toBeVisible();
  },
};

export const ConfigurePrefillObjectsAPI = {
  parameters: {
    msw: {
      handlers: {
        objectTypeTargetPaths: mockTargetPathsPost({
          string: [
            {
              targetPath: ['bsn'],
              isRequired: true,
              jsonSchema: {type: 'string'},
            },
          ],
          number: [
            {
              targetPath: ['path', 'to', 'bsn'],
              isRequired: true,
              jsonSchema: {type: 'string'},
            },
          ],
        }),
      },
    },
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await step('Open configuration modal', async () => {
      const userDefinedVarsTab = await canvas.findByRole('tab', {name: /Gebruikersvariabelen/});
      expect(userDefinedVarsTab).toBeVisible();
      await userEvent.click(userDefinedVarsTab);

      // open modal for configuration
      const editIcon = canvas.getByTitle('Prefill instellen');
      await userEvent.click(editIcon);
      expect(await canvas.findByRole('dialog')).toBeVisible();
    });

    await step('Configure Objects API prefill', async () => {
      const modal = within(await canvas.findByRole('dialog'));
      const pluginDropdown = await canvas.findByLabelText('Plugin');
      expect(pluginDropdown).toBeVisible();
      await userEvent.selectOptions(pluginDropdown, 'Objects API');

      // check mappings
      const variableSelect = await canvas.findByLabelText('Formuliervariabele');
      expect(variableSelect).toBeVisible();
      expect(modal.getByText('Form.io component')).toBeVisible();

      // Wait until the API call to retrieve the prefillAttributes is done
      await waitFor(async () => {
        const prefillPropertySelect = await canvas.findByLabelText(
          'Selecteer een attribuut uit het objecttype'
        );
        expect(prefillPropertySelect).toBeVisible();
        expect(prefillPropertySelect).toHaveValue(serializeValue(['firstName']));
      });
    });
  },
};

export const ConfigurePrefillObjectsAPIWithCopyButton = {
  parameters: {
    msw: {
      handlers: {
        objectTypeTargetPaths: [
          mockTargetPathsPost({
            number: [
              {
                targetPath: ['bsn'],
                isRequired: true,
                jsonSchema: {type: 'string'},
              },
            ],
            string: [
              {
                targetPath: ['path', 'to', 'bsn'],
                isRequired: true,
                jsonSchema: {type: 'string'},
              },
            ],
          }),
        ],
      },
    },
  },
  args: {
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 'group-1',
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          authAttributePath: ['path', 'to', 'bsn'],
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
          objectsApiGroup: 'group-1',
          objecttype: '209e0341-834d-4060-bd19-a3419d19ed74',
          objecttypeVersion: 2,
          authAttributePath: ['path', 'to', 'bsn'],
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
      const userDefinedVarsTab = await canvas.findByRole('tab', {name: /Gebruikersvariabelen/});
      expect(userDefinedVarsTab).toBeVisible();
      await userEvent.click(userDefinedVarsTab);

      // open modal for configuration
      const editIcon = canvas.getByTitle('Prefill instellen');
      await userEvent.click(editIcon);
      expect(await canvas.findByRole('dialog')).toBeVisible();
    });

    await step('Configure Objects API prefill with copy button', async () => {
      const modal = within(await canvas.findByRole('dialog'));
      const pluginDropdown = await canvas.findByLabelText('Plugin');
      expect(pluginDropdown).toBeVisible();
      await userEvent.selectOptions(pluginDropdown, 'Objects API');

      const toggleCopyDropdown = await modal.findByRole('link', {
        name: 'Neem registratie-instellingen over',
      });
      expect(toggleCopyDropdown).toBeVisible();
      await userEvent.click(toggleCopyDropdown);

      const copyButton = await canvas.findByRole('button', {name: 'Overnemen'});
      expect(copyButton).toBeDisabled();
      const copyDropdown = await modal.findByLabelText('Registratie-instellingen overnemen');
      expect(copyDropdown).toBeVisible();
      await rsSelect(copyDropdown, 'Other Objects API registration with a long name');

      expect(copyButton).toBeVisible();
      expect(copyButton).not.toBeDisabled();
      await userEvent.click(copyButton);

      // Click the confirmation button
      const confirmationButton = await canvas.findByRole('button', {name: 'Accepteren'});
      expect(confirmationButton).toBeVisible();
      await userEvent.click(confirmationButton);

      const modalForm = await canvas.findByTestId('modal-form');
      expect(modalForm).toBeVisible();
      await modal.findAllByLabelText('Selecteer een attribuut uit het objecttype');

      // Wait until the API call to retrieve the prefillAttributes is done
      await modal.findByText('path > to > bsn', undefined, {timeout: 2000});

      await waitFor(
        () => {
          expect(modalForm).toHaveFormValues({
            'options.objectsApiGroup': 'group-1',
            'options.objecttypeUuid': '209e0341-834d-4060-bd19-a3419d19ed74',
            'options.objecttypeVersion': '2',
            'options.authAttributePath': JSON.stringify(['path', 'to', 'bsn']),
            'options.variablesMapping.0.targetPath': serializeValue(['path', 'to.the', 'target']),
          });
        },
        {timeout: 5000}
      );
    });
  },
};

export const ConfigurePrefillFamilyMembersPartners = {
  args: {
    availableFormVariables: [
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: undefined,
        name: 'User defined mutable',
        key: 'userDefinedMutable',
        source: 'user_defined',
        dataType: 'array',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
      },
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: undefined,
        name: 'User defined immutable',
        key: 'userDefinedImmutable',
        source: 'user_defined',
        prefillPlugin: 'family_members',
        dataType: 'string',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
        prefillOptions: {
          type: 'partners',
          mutableDataFormVariable: 'userDefinedMutable',
        },
      },
    ],
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await step('Open configuration modal', async () => {
      const userDefinedVarsTab = await canvas.findByRole('tab', {name: /Gebruikersvariabelen/});
      expect(userDefinedVarsTab).toBeVisible();
      await userEvent.click(userDefinedVarsTab);
      // open modal for configuration
      const editIcons = canvas.getAllByTitle('Prefill instellen');
      await userEvent.click(editIcons[1]);
      expect(await canvas.findByRole('dialog')).toBeVisible();
    });

    await step('Configure Family members prefill for partners', async () => {
      const modal = within(await canvas.findByRole('dialog'));
      const pluginDropdown = await canvas.findByLabelText('Plugin');
      expect(pluginDropdown).toBeVisible();
      await userEvent.selectOptions(pluginDropdown, 'Family members');
      // check person type
      const personTypeSelect = await canvas.findByText('Type');
      expect(personTypeSelect).toBeVisible();
      expect(modal.getByText('Partners')).toBeVisible();
      // check mutable form variable
      const mutableDataFormVariableSelect = await canvas.findByText('Bestemmings-variabele');
      expect(mutableDataFormVariableSelect).toBeVisible();
      expect(modal.getByText('User defined mutable')).toBeVisible();
      // check no filters
      const filters = canvas.queryByText('Filters');
      expect(filters).not.toBeInTheDocument();
    });
  },
};

export const ConfigurePrefillFamilyMembersChildren = {
  args: {
    availableFormVariables: [
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: undefined,
        name: 'User defined mutable',
        key: 'userDefinedMutable',
        source: 'user_defined',
        dataType: 'array',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
      },
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: undefined,
        name: 'User defined immutable',
        key: 'userDefinedImmutable',
        source: 'user_defined',
        prefillPlugin: 'family_members',
        dataType: 'string',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
        prefillOptions: {
          type: 'children',
          mutableDataFormVariable: 'userDefinedMutable',
        },
      },
    ],
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await step('Open configuration modal', async () => {
      const userDefinedVarsTab = await canvas.findByRole('tab', {name: /Gebruikersvariabelen/});
      expect(userDefinedVarsTab).toBeVisible();
      await userEvent.click(userDefinedVarsTab);
      // open modal for configuration
      const editIcons = canvas.getAllByTitle('Prefill instellen');
      await userEvent.click(editIcons[1]);
      expect(await canvas.findByRole('dialog')).toBeVisible();
    });

    await step('Configure Family members prefill for partners', async () => {
      const modal = within(await canvas.findByRole('dialog'));
      const pluginDropdown = await canvas.findByLabelText('Plugin');
      expect(pluginDropdown).toBeVisible();
      await userEvent.selectOptions(pluginDropdown, 'Family members');
      // check person type
      const personTypeSelect = await canvas.findByText('Type');
      expect(personTypeSelect).toBeVisible();
      expect(modal.getByText('Kinderen')).toBeVisible();
      // check mutable form variable
      const mutableDataFormVariableSelect = await canvas.findByText('Bestemmings-variabele');
      expect(mutableDataFormVariableSelect).toBeVisible();
      expect(modal.getByText('User defined mutable')).toBeVisible();
    });

    await step('Filters', async () => {
      const minAge = await canvas.findByLabelText('Minimale leeftijd');
      const maxAge = await canvas.findByLabelText('Maximale leeftijd');
      const includeDeceased = await canvas.findByLabelText('Inclusief overledenen');
      expect(minAge).toBeVisible();
      expect(maxAge).toBeVisible();
      expect(includeDeceased).toBeVisible();
    });
  },
};

export const WithValidationErrors = {
  args: {
    availableFormVariables: [
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

    const userDefinedVarsTab = await canvas.findByRole('tab', {name: /Gebruikersvariabelen/});
    expect(userDefinedVarsTab).toBeVisible();
    await userEvent.click(userDefinedVarsTab);

    // open modal for configuration
    const editIcon = canvas.getByTitle('Prefill instellen');
    await userEvent.click(editIcon);
  },
};

export const ConfigurePrefillObjectsAPIWithValidationErrors = {
  args: {
    availableFormVariables: [
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: undefined,
        name: 'User defined',
        key: 'userDefined',
        source: 'user_defined',
        prefillPlugin: 'objects_api',
        prefillAttribute: '',
        prefillIdentifierRole: '',
        dataType: 'string',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: [],
        options: {
          objectsApiGroup: 'group-1',
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          authAttributePath: ['path', 'to', 'bsn'],
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
        errors: {
          prefillPlugin: 'Computer says no.',
          prefillOptions: {
            objectsApiGroup: 'Computer says no.',
            objecttypeUuid: 'Computer says no.',
            objecttypeVersion: 'Computer says no.',
            authAttributePath: 'This list may not be empty.',
          },
        },
      },
    ],
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await step('Open configuration modal', async () => {
      const userDefinedVarsTab = await canvas.findByRole('tab', {name: /Gebruikersvariabelen/});
      expect(userDefinedVarsTab).toBeVisible();
      await userEvent.click(userDefinedVarsTab);

      // open modal for configuration
      const editIcon = canvas.getByTitle('Prefill instellen');
      await userEvent.click(editIcon);
      expect(await canvas.findByRole('dialog')).toBeVisible();
    });

    await step('Verify that error is shown', async () => {
      const error = canvas.getByText('This list may not be empty.');
      expect(error).toBeVisible();
    });
  },
};

export const AddressNLMappingSpecificTargetsNoDeriveAddress = {
  args: {
    availableFormVariables: [
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: 'http://localhost:8000/api/v2/form-definitions/6de1ea5a',
        name: 'AddressNL',
        key: 'addressNl',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataType: 'string',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: {postcode: '', house_letter: '', house_number: '', house_number_addition: ''},
      },
    ],
    availableComponents: {
      addressNl: {
        type: 'addressNL',
        key: 'addressNl',
      },
    },
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 'group-1',
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          variablesMapping: [],
        },
      },
    ],
  },
  parameters: {
    msw: {
      handlers: [
        mockTargetPathsPost({
          object: [
            {
              targetPath: ['other', 'path'],
              isRequired: false,
              jsonSchema: {type: 'object', properties: {a: {type: 'string'}}},
            },
          ],
          string: [
            {
              targetPath: ['path', 'to.the', 'target'],
              isRequired: true,
              jsonSchema: {type: 'string'},
            },
          ],
          number: [
            {
              targetPath: ['number', 'target'],
              isRequired: true,
              jsonSchema: {type: 'number'},
            },
          ],
        }),
      ],
    },
  },

  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    const editIcons = canvas.getAllByTitle('Registratie-instellingen bewerken');
    await userEvent.click(editIcons[0]);

    const modalForm = await canvas.findByTestId('modal-form');
    expect(modalForm).toBeVisible();
    expect(modalForm).toHaveFormValues({});
    const modal = within(modalForm);

    const targetPathDropdown = modal.getByRole('combobox', {name: 'JSON Schema van doelobject'});
    expect(targetPathDropdown).toBeVisible();

    await step('Map entire object', async () => {
      selectEvent.openMenu(targetPathDropdown);

      const targetSelectMenu = within(await findReactSelectMenu(canvas));
      await targetSelectMenu.findByRole('option', {name: 'other > path'});
      expect(targetSelectMenu.getAllByRole('option')).toHaveLength(1);

      await rsSelect(targetPathDropdown, 'other > path');
    });

    await step('Map specific subfields', async () => {
      await selectEvent.clearAll(targetPathDropdown);

      const specificTargetsCheckbox = canvas.getByRole('checkbox', {
        name: 'Koppel individuele velden',
      });
      await userEvent.click(specificTargetsCheckbox);

      const postcodeSelect = await canvas.findByLabelText('Bestemmingspad postcode');
      expect(postcodeSelect).toBeVisible();

      const houseNumberSelect = await canvas.findByLabelText('Bestemmingspad huisnummer');
      expect(houseNumberSelect).toBeVisible();

      const houseLetterSelect = await canvas.findByLabelText('Bestemmingspad huisletter');
      expect(houseLetterSelect).toBeVisible();

      const houseNumberAdditionSelect = await canvas.findByLabelText(
        'Bestemmingspad huisnummertoevoeging'
      );
      expect(houseNumberAdditionSelect).toBeVisible();

      const citySelect = await canvas.findByLabelText('Bestemmingspad stad/gemeente');
      expect(citySelect).toBeDisabled();

      const streetNameSelect = await canvas.findByLabelText('Bestemmingspad straatnaam');
      expect(streetNameSelect).toBeDisabled();

      await rsSelect(postcodeSelect, 'path > to.the > target (verplicht)');
      await rsSelect(houseNumberSelect, 'number > target (verplicht)');
    });
  },
};

export const AddressNLMappingSpecificTargetsDeriveAddress = {
  args: {
    availableFormVariables: [
      {
        form: 'http://localhost:8000/api/v2/forms/36612390',
        formDefinition: 'http://localhost:8000/api/v2/form-definitions/6de1ea5a',
        name: 'AddressNL',
        key: 'addressNl',
        source: 'component',
        prefillPlugin: '',
        prefillAttribute: '',
        prefillIdentifierRole: 'main',
        dataType: 'string',
        dataFormat: undefined,
        isSensitiveData: false,
        serviceFetchConfiguration: undefined,
        initialValue: {postcode: '', house_letter: '', house_number: '', house_number_addition: ''},
        deriveAddress: true,
      },
    ],
    availableComponents: {
      addressNl: {
        type: 'addressNL',
        key: 'addressNl',
        deriveAddress: true,
      },
    },
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objectsApiGroup: 'group-1',
          objecttype: '2c77babf-a967-4057-9969-0200320d23f1',
          objecttypeVersion: 2,
          variablesMapping: [],
        },
      },
    ],
  },
  parameters: {
    msw: {
      handlers: [
        mockTargetPathsPost({
          object: [
            {
              targetPath: ['other', 'path'],
              isRequired: false,
              jsonSchema: {type: 'object', properties: {a: {type: 'string'}}},
            },
          ],
          string: [
            {
              targetPath: ['path', 'to.the', 'target'],
              isRequired: true,
              jsonSchema: {type: 'string'},
            },
          ],
          number: [
            {
              targetPath: ['number', 'target'],
              isRequired: true,
              jsonSchema: {type: 'number'},
            },
          ],
        }),
      ],
    },
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const editIcons = canvas.getAllByTitle('Registratie-instellingen bewerken');
    await userEvent.click(editIcons[0]);

    const modalForm = await canvas.findByTestId('modal-form');
    const modal = within(modalForm);

    const targetPathDropdown = modal.getByRole('combobox', {name: 'JSON Schema van doelobject'});
    expect(targetPathDropdown).toBeVisible();

    const specificTargetsCheckbox = canvas.getByRole('checkbox', {
      name: 'Koppel individuele velden',
    });
    await userEvent.click(specificTargetsCheckbox);

    const postcodeSelect = await canvas.findByLabelText('Bestemmingspad postcode');
    expect(postcodeSelect).toBeVisible();

    const houseNumberSelect = await canvas.findByLabelText('Bestemmingspad huisnummer');
    expect(houseNumberSelect).toBeVisible();

    const houseLetterSelect = await canvas.findByLabelText('Bestemmingspad huisletter');
    expect(houseLetterSelect).toBeVisible();

    const houseNumberAdditionSelect = await canvas.findByLabelText(
      'Bestemmingspad huisnummertoevoeging'
    );
    expect(houseNumberAdditionSelect).toBeVisible();

    const citySelect = await canvas.findByLabelText('Bestemmingspad stad/gemeente');
    expect(citySelect).toBeVisible();
    expect(citySelect).not.toBeDisabled();

    const streetNameSelect = await canvas.findByLabelText('Bestemmingspad straatnaam');
    expect(streetNameSelect).toBeVisible();
    expect(streetNameSelect).not.toBeDisabled();
  },
};

export const TwoBackendsWhereOnlyOneIntroducesRegistrationVariables = {
  args: {
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {},
      },
      {
        backend: 'testPlugin',
        key: 'test_backend',
        name: 'Example test registration',
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
    ],
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const registrationTab = canvas.getByRole('tab', {name: 'Registratie'});
    await userEvent.click(registrationTab);

    // With multiple backends configured, but only one of them introduces registration variables,
    // the plugin heading should be visible.
    expect(canvas.getByRole('heading', {name: 'Objects API registration'})).toBeVisible();
  },
};
