import {fn} from '@storybook/test';

import {FormDecorator} from 'components/admin/form_design/story-decorators';

import {SynchronizeVariablesActionConfig} from './SynchronizeVariablesConfigModal';

export default {
  title: 'Form design/FormLogic/SynchronizeVariables Action configuration',
  component: SynchronizeVariablesActionConfig,
  decorators: [FormDecorator],
  argTypes: {},
  args: {
    initialValues: {
      sourceVariable: '',
      destinationVariable: '',
      identifierVariable: '',
      dataMappings: [],
    },
    availableComponents: {
      children: {
        key: 'children',
        type: 'children',
        label: 'Children',
      },
      editgrid: {
        key: 'editgrid',
        type: 'editgrid',
        label: 'Editgrid',
        components: [
          {
            key: 'bsn',
            type: 'bsn',
            label: 'BSN',
          },
          {
            key: 'firstNames',
            type: 'textfield',
            label: 'First names',
          },
        ],
      },
      'editgrid.bsn': {
        key: 'bsn',
        type: 'bsn',
        label: 'BSN',
      },
      'editgrid.firstNames': {
        key: 'firstNames',
        type: 'textfield',
        label: 'First names',
      },
    },
    availableFormVariables: [
      {
        dataFormat: '',
        dataType: 'array',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'children',
        name: 'children',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'component',
      },
      {
        dataFormat: '',
        dataType: 'array',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'editgrid',
        name: 'editgrid',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'component',
      },
    ],
    onSave: fn(),
  },
};

export const Default = {
  args: {
    initialValues: {
      sourceVariable: '',
      destinationVariable: '',
      identifierVariable: '',
      dataMappings: [],
    },
  },
};

export const withInitialValues = {
  args: {
    initialValues: {
      sourceVariable: 'children',
      destinationVariable: 'editgrid',
      identifierVariable: 'bsn',
      dataMappings: [{componentKey: 'bsn', property: 'bsn'}],
    },
  },
};

export const EmptyMappingsErrors = {
  args: {
    initialValues: {
      sourceVariable: 'children',
      destinationVariable: 'editgrid',
      identifierVariable: 'bsn',
      dataMappings: [],
    },
    errors: {
      dataMappings: {nonFieldErrors: 'At least one mapping is needed'},
    },
  },
};

export const IdentifierMissingErrors = {
  args: {
    initialValues: {
      sourceVariable: 'children',
      destinationVariable: 'editgrid',
      identifierVariable: 'bsn',
      dataMappings: [],
    },
    errors: {
      dataMappings: 'No mapping for the identifier',
    },
  },
};

export const EmptyFieldErrors = {
  args: {
    initialValues: {
      sourceVariable: '',
      destinationVariable: 'editgrid',
      identifierVariable: 'bsn',
      dataMappings: [{componentKey: 'bsn', property: 'bsn'}],
    },
    errors: {sourceVariable: 'This field is required'},
  },
};
