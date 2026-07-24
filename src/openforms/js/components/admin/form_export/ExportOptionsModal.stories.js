import {expect, fn, userEvent, within} from 'storybook/test';

import {FormDecorator} from 'components/admin/form_design/story-decorators';
import {VARIABLE_SOURCES} from 'components/admin/form_design/variables/constants';

import ExportOptionsModal from './ExportOptionsModal';

export default {
  title: 'Admin / Form export options modal',
  component: ExportOptionsModal,
  decorators: [FormDecorator],
  args: {
    isOpen: true,
    onSubmit: fn(),
    onCloseModal: fn(),
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {},
      },
    ],
    availableFormVariables: [
      {
        form: 'bar',
        formDefinition: 'foo',
        name: 'Name',
        key: 'key',
        source: VARIABLE_SOURCES.userDefined,
        prefillPlugin: 'demo',
      },
    ],
    form: {
      authBackends: [
        {
          backend: 'yivi_oidc',
          options: {
            additionalAttributesGroups: ['be5e0bd1-d3be-4004-b37b-a4ce1bc68664'],
          },
        },
      ],
      paymentBackend: 'demo',
      category: 'http://localhost/api/v2/public/categories/be5e0bd1-d3be-4004-b37b-a4ce1bc68664',
      product: 'http://localhost/api/v2/products/be5e0bd1-d3be-4004-b37b-a4ce1bc68664',
      theme: 'http://localhost/api/v2/themes/be5e0bd1-d3be-4004-b37b-a4ce1bc68664',
    },
    availableComponents: [
      {
        type: 'map',
        id: 'map',
        key: 'map',
        label: 'Map field',
        tileLayerIdentifier: 'map-background-identifier',
        overlays: [
          {
            label: 'Overlay 1',
            uuid: 'be5e0bd1-d3be-4004-b37b-a4ce1bc68664',
          },
        ],
      },
    ],
  },
};

export const Default = {
  play: async ({canvasElement, step, args}) => {
    const canvas = within(canvasElement);
    const exportButton = canvas.getByRole('button', {name: 'Formulier exporteren'});

    const sensitiveContentField = canvas.getByLabelText('Anonimiseer formulierinstellingen');

    const registrationBackendsInput = canvas.getByLabelText('Registratie backends');
    const prefillInput = canvas.getByLabelText('Prefill');
    const paymentBackendInput = canvas.getByLabelText('Betaalprovider');
    const authBackendsInput = canvas.getByLabelText('Authenticatie plugins');

    const productInput = canvas.getByLabelText('Product');
    const wmsTileLayersInput = canvas.getByLabelText('WMS-kaartlagen');
    const wmtsTileLayersInput = canvas.getByLabelText('WMTS-kaartlagen');
    const yiviAttributeGroupsInput = canvas.getByLabelText('Yivi attribuut groepen');
    const themeInput = canvas.getByLabelText('Thema');
    const categoryInput = canvas.getByLabelText('Categorie');

    await step('Initial state', () => {
      // All inputs should be visible
      expect(sensitiveContentField).toBeVisible();

      expect(registrationBackendsInput).toBeVisible();
      expect(prefillInput).toBeVisible();
      expect(paymentBackendInput).toBeVisible();
      expect(authBackendsInput).toBeVisible();

      expect(productInput).toBeVisible();
      expect(wmsTileLayersInput).toBeVisible();
      expect(wmtsTileLayersInput).toBeVisible();
      expect(yiviAttributeGroupsInput).toBeVisible();
      expect(themeInput).toBeVisible();
      expect(categoryInput).toBeVisible();

      // The sensitive content field and form data inputs should be checked
      expect(sensitiveContentField).toBeChecked();
      expect(registrationBackendsInput).toBeChecked();
      expect(prefillInput).toBeChecked();
      expect(paymentBackendInput).toBeChecked();
      expect(authBackendsInput).toBeChecked();

      // The additional form data inputs should be unchecked
      expect(productInput).not.toBeChecked();
      expect(wmsTileLayersInput).not.toBeChecked();
      expect(wmtsTileLayersInput).not.toBeChecked();
      expect(yiviAttributeGroupsInput).not.toBeChecked();
      expect(themeInput).not.toBeChecked();
      expect(categoryInput).not.toBeChecked();
    });

    await step('Make selection state', async () => {
      await userEvent.click(sensitiveContentField);
      expect(sensitiveContentField).not.toBeChecked();

      await userEvent.click(registrationBackendsInput);
      await userEvent.click(paymentBackendInput);
      expect(registrationBackendsInput).not.toBeChecked();
      expect(paymentBackendInput).not.toBeChecked();

      await userEvent.click(wmsTileLayersInput);
      await userEvent.click(wmtsTileLayersInput);
      await userEvent.click(yiviAttributeGroupsInput);
      expect(wmsTileLayersInput).toBeChecked();
      expect(wmtsTileLayersInput).toBeChecked();
      expect(yiviAttributeGroupsInput).toBeChecked();
    });

    await step('Confirm export', async () => {
      await userEvent.click(exportButton);
      expect(args.onSubmit).toHaveBeenCalledWith({
        removeSensitiveContent: false,
        formConfiguration: ['prefill', 'authBackends'],
        additionalFormConfiguration: ['wmsTileLayers', 'wmtsTileLayers', 'yiviAttributeGroups'],
      });
    });
  },
};

export const WithoutRegistrationBackends = {
  args: {
    registrationBackends: [],
  },
  play: async ({canvasElement, args}) => {
    const canvas = within(canvasElement);
    const exportButton = canvas.getByRole('button', {name: 'Formulier exporteren'});

    const registrationBackendsInput = canvas.queryByLabelText('Registratie backends');
    expect(registrationBackendsInput).not.toBeInTheDocument();

    await userEvent.click(exportButton);
    expect(args.onSubmit).toHaveBeenCalledWith({
      removeSensitiveContent: true,
      formConfiguration: ['prefill', 'paymentBackend', 'authBackends'],
      additionalFormConfiguration: [],
    });
  },
};

export const WithOnlyRemoveSensitiveDataOption = {
  args: {
    registrationBackends: [],
    availableFormVariables: [
      {
        form: 'bar',
        formDefinition: 'foo',
        name: 'Name',
        key: 'key',
        source: VARIABLE_SOURCES.userDefined,
      },
    ],
    form: {
      authBackends: [],
      paymentBackend: '',
      category: '',
      product: '',
      theme: '',
    },
    availableComponents: [
      {
        type: 'textfield',
        id: 'textfield',
        key: 'textfield',
        label: 'Textfield',
      },
    ],
  },
  play: async ({canvasElement, args}) => {
    const canvas = within(canvasElement);
    const exportButton = canvas.getByRole('button', {name: 'Formulier exporteren'});

    await userEvent.click(exportButton);
    expect(args.onSubmit).toHaveBeenCalledWith({
      removeSensitiveContent: true,
      formConfiguration: [],
      additionalFormConfiguration: [],
    });
  },
};
