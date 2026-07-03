import {expect, fn, userEvent, within} from 'storybook/test';

import ExportOptionsModal from './ExportOptionsModal';

export default {
  title: 'Admin / Form import & export / ExportOptionsModal',
  component: ExportOptionsModal,
  args: {
    isOpen: true,
    onCloseModal: fn(),
  },
};

export const Default = {
  play: async ({canvasElement, step, args}) => {
    const canvas = within(canvasElement);

    const sensitiveContentField = canvas.getByLabelText('Anonimiseer formulierinstellingen');

    const registrationBackendsInput = canvas.getByLabelText('Registratie backends');
    const prefillInput = canvas.getByLabelText('Prefill');
    const paymentBackendInput = canvas.getByLabelText('Betaalprovider');

    const productInput = canvas.getByLabelText('Product');
    const wmsTileLayersInput = canvas.getByLabelText('WMS-kaartlagen');
    const wmtsTileLayersInput = canvas.getByLabelText('WMTS-kaartlagen');
    const yiviAttributeGroupsInput = canvas.getByLabelText('Yivi attribuut groepen');
    const themeInput = canvas.getByLabelText('Thema');
    const categoryInput = canvas.getByLabelText('Categorie');

    step('Initial state', () => {
      // All inputs should be visible
      expect(sensitiveContentField).toBeVisible();

      expect(registrationBackendsInput).toBeVisible();
      expect(prefillInput).toBeVisible();
      expect(paymentBackendInput).toBeVisible();

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
  },
};
