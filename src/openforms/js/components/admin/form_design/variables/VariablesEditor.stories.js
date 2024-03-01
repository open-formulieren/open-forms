import {mockTargetPathsPost} from 'components/admin/form_design/registrations/objectsapi/mocks';

import {FormDecorator} from '../story-decorators';
import VariablesEditor from './VariablesEditor';

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
        key: 'objects_api',
        name: 'Example Objects API reg.',
        options: {
          version: 2,
          objecttype:
            'https://objecttypen.nl/api/v1/objecttypes/2c77babf-a967-4057-9969-0200320d23f1',
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
        key: 'objects_api',
        name: 'Other Objects API registration with a long name',
        options: {
          version: 2,
          objecttype:
            'https://objecttypen.nl/api/v1/objecttypes/209e0341-834d-4060-bd19-a3419d19ed74',
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
        key: 'objects_api',
        name: "Shouldn't display!",
        options: {
          version: 1,
          objecttype:
            'https://objecttypen.nl/api/v1/objecttypes/209e0341-834d-4060-bd19-a3419d19ed74',
          objecttypeVersion: 2,
        },
      },
    ],
    onFieldChange: data => {
      console.log(data);
    },
  },
  parameters: {
    msw: {
      handlers: [
        mockTargetPathsPost([
          {
            targetPath: ['path', 'to.the', 'target'],
            required: true,
            jsonSchema: {type: 'string'},
          },
          {
            targetPath: ['other', 'path'],
            required: false,
            jsonSchema: {type: 'object', properties: {a: {type: 'string'}}, required: ['a']},
          },
        ]),
      ],
    },
  },
};
