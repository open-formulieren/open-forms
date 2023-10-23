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
  },
  argTypes: {
    onChange: {action: true},
  },
};

export const Default = {};
