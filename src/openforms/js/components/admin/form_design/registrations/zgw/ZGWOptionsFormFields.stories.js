import {fn, userEvent, within} from '@storybook/test';
import {Form, Formik} from 'formik';
import selectEvent from 'react-select-event';

import {
  FeatureFlagsDecorator,
  FormDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';

import ZGWFormFields from './ZGWOptionsFormFields';
import {mockCaseTypesGet, mockCataloguesGet} from './mocks';

const NAME = 'form.registrationBackends.0.options';

const render = ({apiGroups, confidentialityLevelChoices, formData}) => (
  <Formik initialValues={formData} onSubmit={fn()}>
    <Form data-testid="test-form">
      <ZGWFormFields
        index={0}
        name={NAME}
        apiGroupChoices={apiGroups}
        confidentialityLevelChoices={confidentialityLevelChoices}
      />
    </Form>
  </Formik>
);

export default {
  title: 'Form design/Registration/ZGW',
  component: ZGWFormFields,
  decorators: [ValidationErrorsDecorator, FormDecorator, FeatureFlagsDecorator],
  render,
  args: {
    apiGroups: [[1, 'ZGW API']],
    confidentialityLevelChoices: [
      ['openbaar', 'Openbaar'],
      ['geheim', 'Geheim'],
    ],
    formData: {},
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
      handlers: [mockCataloguesGet(), mockCaseTypesGet()],
    },
  },
};

export const Default = {
  args: {
    formData: {
      zgwApiGroup: 1,
      zaaktype: 'https://example.com',
      propertyMappings: [
        {eigenschap: 'Property 1', componentKey: 'textField1'},
        {eigenschap: '', componentKey: ''},
      ],
    },
  },
};

export const ValidationErrorsBaseTab = {
  args: {
    validationErrors: [
      [`${NAME}.zgwApiGroup`, 'Computer says no'],
      [`${NAME}.zaaktype`, 'Computer says no'],
      [`${NAME}.informatieobjecttype`, 'Computer says no'],
      [`${NAME}.organisatieRsin`, 'Computer says no'],
      [`${NAME}.zaakVertrouwelijkheidaanduiding`, 'Computer says no'],
      [`${NAME}.medewerkerRoltype`, 'Computer says no'],
      [`${NAME}.objecttype`, 'Computer says no'],
      [`${NAME}.objecttypeVersion`, 'Computer says no'],
      [`${NAME}.contentJson`, 'Computer says no'],
    ],
  },
};

export const ValidationErrorsCasePropertiesTab = {
  args: {
    formData: {
      propertyMappings: [{eigenschap: '', componentKey: ''}],
    },
    validationErrors: [
      [`${NAME}.propertyMappings.0.componentKey`, 'Computer says no'],
      [`${NAME}.propertyMappings.0.eigenschap`, 'Computer says no'],
    ],
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('tab', {name: /Zaakeigenschappen/}));
  },
};

export const SelectCaseType = {
  args: {
    formData: {
      zgwApiGroup: 1,
      zaaktype: '',
      propertyMappings: [],
    },
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const catalogueSelect = canvas.getByLabelText('Catalogus');
    await selectEvent.select(catalogueSelect, 'Catalogus 1');

    const caseTypeSelect = canvas.getByLabelText('Zaaktype', {
      selector: '#id_caseTypeIdentification',
    });
    await selectEvent.select(caseTypeSelect, 'Request passport');
  },
};
