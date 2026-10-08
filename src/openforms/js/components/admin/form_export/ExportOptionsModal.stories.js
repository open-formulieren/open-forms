import {FormDecorator} from '@/sb-decorators';
import {expect, fn, userEvent, within} from 'storybook/test';

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
    registrationBackends: [
      {
        backend: 'objects_api',
        key: 'objects_api_1',
        name: 'Example Objects API reg.',
        options: {},
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
      payment: {
        backend: 'demo',
        options: {},
      },
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

    const registrationBackendsInput = canvas.getByLabelText('Registratieplugins');
    const prefillInput = canvas.getByLabelText('Prefill');
    const paymentBackendInput = canvas.getByLabelText('Betaalprovider');
    const authBackendsInput = canvas.getByLabelText('Authenticatieplugins');

    const productInput = canvas.getByLabelText('Product');
    const wmsTileLayersInput = canvas.getByLabelText('WMS-kaartlagen');
    const wmtsTileLayersInput = canvas.getByLabelText('Kaartachtergrondlagen');
    const yiviAttributeGroupsInput = canvas.getByLabelText('Yivi-attribuutgroepen');

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

    const registrationBackendsInput = canvas.queryByLabelText('Registratieplugins');
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
    availableFormVariables: [
      {
        form: 'bar',
        formDefinition: 'foo',
        name: 'Name',
        key: 'key',
        source: VARIABLE_SOURCES.userDefined,
      },
    ],
    registrationBackends: [],
    form: {
      authBackends: [],
      payment: {
        backend: '',
        options: {},
      },
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
