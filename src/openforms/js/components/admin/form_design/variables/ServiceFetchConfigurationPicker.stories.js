import {FormLogicDecorator} from '../story-decorators';
import ServiceFetchConfigurationPicker from './ServiceFetchConfigurationPicker';

export default {
  title: 'Form design/Service Fetch/ServiceFetchConfigurationPicker',
  decorators: [FormLogicDecorator],
  component: ServiceFetchConfigurationPicker,
};

export const Blank = {
  name: 'Blank',

  args: {
    availableServices: [
      {
        url: 'http://foo.com/services/1',
        label: 'Service 1',
        apiRoot: 'http://foo.com/api/v1/',
        apiType: 'ORC',
      },
      {
        url: 'http://foo.com/services/2',
        label: 'Service 2',
        apiRoot: 'http://bar.com/api/v1/',
        apiType: 'ORC',
      },
    ],

    serviceFetchConfigurations: [
      {
        name: 'Foo fetch',
        id: 1,
        service: 'http://foo.com/services/1',
        path: '/some-path',
        method: 'GET',
        headers: [['X-Foo', 'foo']],
        queryParams: [['parameter2', ['value1', 'value2']]],

        body: {
          field1: 'value',
          field2: 'value2',
        },

        dataMappingType: 'jq',
        mappingExpression: '.field.nested',
      },
      {
        name: '', // No name supplied, should fall back to "method path (service)"
        id: 2,
        service: 'http://foo.com/services/2',
        path: '/some-other-path',
        method: 'POST',
        headers: [['X-Foo', 'bar']],
        queryParams: [
          ['parameter', ['value']],
          ['parameter2', ['value1', 'value2']],
        ],

        body: {
          field1: 'value',
          field2: 'value2',
        },

        dataMappingType: 'JsonLogic',

        mappingExpression: {
          var: 'field',
        },
      },
    ],
  },
};
