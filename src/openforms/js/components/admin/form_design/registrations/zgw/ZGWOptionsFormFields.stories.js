import {fn, userEvent, within} from '@storybook/test';
import {Form, Formik} from 'formik';

import {
  FeatureFlagsDecorator,
  FormDecorator,
  FormModalContentDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';
import {rsSelect} from 'utils/storybookTestHelpers';

import ZGWFormFields from './ZGWOptionsFormFields';
import {
  mockCaseTypesGet,
  mockCataloguesGet,
  mockCataloguesGetError,
  mockDocumenTypesGet,
  mockProductsGet,
  mockRoleTypesGet,
} from './mocks';

const NAME = 'form.registrationBackends.0.options';

const render = ({apiGroups, objectsApiGroupChoices, confidentialityLevelChoices, formData}) => (
  <Formik
    initialValues={{
      // defaults
      caseTypeIdentification: '',
      documentTypeDescription: '',
      zaaktype: '',
      informatieobjecttype: '',
      organisatieRsin: '',
      zaakVertrouwelijkheidaanduiding: '',
      medewerkerRoltype: '',
      partnersRoltype: '',
      partnersDescription: '',
      propertyMappings: [],
      productUrl: '',
      // Ensure that this is explicitly set to null instead of undefined,
      // because the field is required by the serializer
      objectsApiGroup: null,
      // saved data, overwrites defaults
      ...formData,
    }}
    onSubmit={fn()}
  >
    <Form data-testid="test-form">
      <ZGWFormFields
        index={0}
        name={NAME}
        apiGroupChoices={apiGroups}
        objectsApiGroupChoices={objectsApiGroupChoices}
        confidentialityLevelChoices={confidentialityLevelChoices}
      />
    </Form>
  </Formik>
);

export default {
  title: 'Form design/Registration/ZGW',
  component: ZGWFormFields,
  decorators: [
    ValidationErrorsDecorator,
    FormDecorator,
    FeatureFlagsDecorator,
    FormModalContentDecorator,
  ],
  render,
  args: {
    apiGroups: [
      [1, 'ZGW API'],
      [2, 'ZGW API 2'],
    ],
    objectsApiGroupChoices: [['objects-group', 'Objects API']],
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
      handlers: {
        catalogues: [mockCataloguesGet()],
        caseTypes: [mockCaseTypesGet()],
        documentTypes: [mockDocumenTypesGet()],
        roleTypes: [mockRoleTypesGet()],
        products: [mockProductsGet()],
      },
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
      [`${NAME}.catalogue`, 'Computer says no'],
      [`${NAME}.caseTypeIdentification`, 'Computer says no'],
      [`${NAME}.documentTypeDescription`, 'Computer says no'],
      [`${NAME}.zaaktype`, 'Computer says no'],
      [`${NAME}.informatieobjecttype`, 'Computer says no'],
      [`${NAME}.organisatieRsin`, 'Computer says no'],
      [`${NAME}.zaakVertrouwelijkheidaanduiding`, 'Computer says no'],
      [`${NAME}.medewerkerRoltype`, 'Computer says no'],
      [`${NAME}.partnersRoltype`, 'Computer says no'],
      [`${NAME}.partnersDescription`, 'Computer says no'],
      [`${NAME}.productUrl`, 'Computer says no'],
      [`${NAME}.objectsApiGroup`, 'Computer says no'],
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

export const SelectCaseTypeAndDocumentType = {
  args: {
    formData: {
      zgwApiGroup: 1,
      zaaktype: '',
      propertyMappings: [],
    },
  },

  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await step('Select catalogue', async () => {
      const catalogueSelect = canvas.getByLabelText('Catalogus');
      await rsSelect(catalogueSelect, 'Catalogus 1');
    });

    await step('Select case type', async () => {
      const caseTypeSelect = canvas.getByLabelText('Zaaktype', {
        selector: '#id_caseTypeIdentification',
      });
      await rsSelect(caseTypeSelect, 'Request passport');
    });

    await step('Select document type', async () => {
      const documentTypeSelect = canvas.getByLabelText('Documenttype', {
        selector: '#id_documentTypeDescription',
      });
      await rsSelect(documentTypeSelect, 'Attachment');
    });

    await step('Select employee role type', async () => {
      const roleTypeSelect = canvas.getByLabelText('Medewerkerroltype');
      await rsSelect(roleTypeSelect, 'Baliemedewerker');
    });

    await step('Select product', async () => {
      const productSelect = canvas.getByLabelText('Product');
      await rsSelect(productSelect, 'Product 1423');
    });
  },
};

export const CataloguesLoadingFails = {
  args: {
    formData: {
      zgwApiGroup: 1,
      zaaktype: '',
      propertyMappings: [],
    },
  },
  parameters: {
    msw: {
      handlers: {
        catalogues: [mockCataloguesGetError()],
      },
    },
  },
};

export const RenderLegacyRoltype = {
  args: {
    formData: {
      zgwApiGroup: 1,
      zaaktype: 'https://example.com/catalogi/api/v1/zaaktypen/123',
      propertyMappings: [],
      medewerkerRoltype: 'Baliemedewerker',
    },
  },
};
