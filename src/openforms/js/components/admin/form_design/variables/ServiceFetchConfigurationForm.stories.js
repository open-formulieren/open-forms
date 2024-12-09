import {useFormik} from 'formik';

import {
  AdminChangeFormDecorator,
  FormLogicDecorator,
} from 'components/admin/form_design/story-decorators';

import ServiceFetchConfigurationForm from './ServiceFetchConfigurationForm';

const Template = ({initialValues = {}, selectExisting}) => {
  const formik = useFormik({
    initialValues: {
      method: 'GET',
      service: '',
      path: '',
      queryParams: [],
      headers: [],
      body: '',
      dataMappingType: '',
      mappingExpression: '',
      ...initialValues,
    },
    onSubmit: values => {
      alert(JSON.stringify(values, null, 2));
    },
  });
  return <ServiceFetchConfigurationForm formik={formik} selectExisting={selectExisting} />;
};

export default {
  title: 'Form design/Service Fetch/ServiceFetchConfigurationForm',
  decorators: [FormLogicDecorator, AdminChangeFormDecorator],
  component: ServiceFetchConfigurationForm,
  render: Template.bind({}),

  argTypes: {
    formik: {
      table: {
        disable: true,
      },
    },
  },
};

export const Blank = {
  name: 'Blank',

  args: {
    availableServices: [
      {
        label: 'Service 1',
        apiRoot: 'http://foo.com/api/v1/',
        apiType: 'ORC',
      },
      {
        label: 'Service 2',
        apiRoot: 'http://bar.com/api/v1/',
        apiType: 'ORC',
      },
    ],

    selectExisting: false,
  },
};

export const Interpolation = {
  name: 'Interpolation',

  args: {
    availableServices: [
      {
        url: 'http://foo.com/services/1',
        label: 'Service 1',
        apiRoot: 'http://foo.com/api/v1/',
        apiType: 'ORC',
      },
    ],

    selectExisting: false,

    initialValues: {
      service: 'http://foo.com/services/1',
      path: 'some/{myUserDefinedVariable}/path',
      queryParams: [
        ['bsn', ['{auth_bsn}']],
        ['fields', ['voornamen', 'geslachtsnaam']],
      ],
      headers: [
        ['X-Environment', 'env={environment}'],
        ['Api-Version', '1.3.2'],
      ],
      dataMappingType: 'jq',
      jqExpression: '._embedded.inp',
    },
  },
};
