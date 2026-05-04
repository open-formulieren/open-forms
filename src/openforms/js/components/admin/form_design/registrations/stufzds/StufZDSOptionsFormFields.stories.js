import {Form, Formik} from 'formik';
import {expect, fn, userEvent, within} from 'storybook/test';

import {
  FeatureFlagsDecorator,
  FormDecorator,
  FormModalContentDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';
import {rsSelect} from 'utils/storybookTestHelpers';

import StufZDSOptionsFormFields from './StufZDSOptionsFormFields';

const FormikDecorator = Story => {
  return (
    <Formik
      initialValues={{
        // defaults
        zdsZaaktypeCode: '',
        zdsZaaktypeOmschrijving: '',
        zdsZaaktypeStatusCode: '',
        zdsZaaktypeStatusOmschrijving: '',
        zdsDocumenttypeOmschrijvingInzending: '',
        zdsZaakdocVertrouwelijkheid: '',
        variablesMapping: [],
      }}
      onSubmit={fn()}
    >
      <Form data-testid="test-form">
        <Story />
      </Form>
    </Formik>
  );
};

export default {
  title: 'Form design/Registration/StUF-ZDS',
  component: StufZDSOptionsFormFields,
  decorators: [
    FormikDecorator,
    ValidationErrorsDecorator,
    FormDecorator,
    FeatureFlagsDecorator,
    FormModalContentDecorator,
  ],
  args: {
    name: 'form.registrationBackends.0.options',
    schema: {
      type: 'object',
      properties: {
        zdsZaakdocVertrouwelijkheid: {
          type: 'string',
          enum: [
            'ZEER GEHEIM',
            'GEHEIM',
            'CONFIDENTIEEL',
            'VERTROUWELIJK',
            'ZAAKVERTROUWELIJK',
            'INTERN',
            'BEPERKT OPENBAAR',
            'OPENBAAR',
          ],
          enumNames: [
            'Zeer geheim',
            'Geheim',
            'Confidentieel',
            'Vertrouwelijk',
            'Zaakvertrouwelijk',
            'Intern',
            'Beperkt openbaar',
            'Openbaar',
          ],
          title: 'Document confidentiality level',
          description:
            'Indication of the level to which extend the dossier of the ZAAK is meant to be public. This is set on the documents created for the ZAAK.',
        },
      },
    },
    availableComponents: {
      textField1: {
        label: 'textfield1',
      },
      textField2: {
        label: 'textfield2',
      },
    },
    availableFormVariables: [
      {
        dataFormat: '',
        dataType: 'string',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'textField1',
        name: 'textfield1',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'component',
      },
      {
        dataFormat: '',
        dataType: 'string',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'textField2',
        name: 'textfield2',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'component',
      },
      {
        dataFormat: '',
        dataType: 'string',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'userDefinedVar1',
        name: 'User defined string',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'user_defined',
      },
      {
        dataFormat: '',
        dataType: 'array',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: [],
        isSensitiveData: false,
        key: 'userDefinedVar2',
        name: 'User defined array',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'user_defined',
      },
      {
        dataFormat: '',
        dataType: 'float',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: null,
        isSensitiveData: false,
        key: 'userDefinedVar3',
        name: 'User defined float',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'user_defined',
      },
    ],
    registrationPluginsVariables: [
      {
        pluginIdentifier: 'stuf-zds-create-zaak',
        pluginVerboseName: 'StUF-ZDS',
        pluginVariables: [
          {
            form: null,
            formDefinition: null,
            name: 'Payment completed',
            key: 'payment_completed',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'boolean',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
          {
            form: null,
            formDefinition: null,
            name: 'Payment amount',
            key: 'payment_amount',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'float',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
          {
            form: null,
            formDefinition: null,
            name: 'Payment public order IDs',
            key: 'payment_public_order_ids',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'array',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
          {
            form: null,
            formDefinition: null,
            name: 'Provider payment IDs',
            key: 'provider_payment_ids',
            source: '',
            serviceFetchConfiguration: null,
            prefillPlugin: '',
            prefillAttribute: '',
            prefillIdentifierRole: 'main',
            prefillOptions: {},
            dataType: 'array',
            dataFormat: '',
            isSensitiveData: false,
            initialValue: null,
          },
        ],
      },
    ],
  },
};

export const VariablesMappingWithCSVSerialize = {
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('tab', {name: /Extra elementen/}));
    const addVariableButton = canvas.getAllByRole('button', {name: /Variabele toevoegen/})[0];
    await userEvent.click(addVariableButton);

    const formVarSelect1 = canvas.getByLabelText('Formuliervariabele');
    await rsSelect(formVarSelect1, 'Payment public order IDs');

    await userEvent.click(addVariableButton);
    const formVarSelect2 = canvas.getAllByLabelText('Formuliervariabele')[1];
    await rsSelect(formVarSelect2, 'Payment completed');

    expect(await canvas.findAllByRole('checkbox')).toHaveLength(1);
  },
};
