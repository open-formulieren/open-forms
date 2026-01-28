import {useState} from 'react';
import {expect, userEvent, within} from 'storybook/test';

import ActionButton from 'components/admin/forms/ActionButton';

import useConfirm from './useConfirm';

const ButtonWithUseConfirm = () => {
  const {ConfirmationModal, confirmationModalProps, openConfirmationModal} = useConfirm();
  const [confirmationResult, setConfirmationResult] = useState(null);
  return (
    <div>
      <ActionButton
        text="Open confirmation modal"
        onClick={async () => {
          const result = await openConfirmationModal();
          setConfirmationResult(result);
        }}
      />
      {confirmationResult !== null ? (
        <p>Confirmation result: {confirmationResult.toString()}</p>
      ) : null}
      <ConfirmationModal
        {...confirmationModalProps}
        title="The confirmation title"
        message="A sample confirmation message"
      />
    </div>
  );
};

export default {
  title: 'Admin / Custom / UseConfirm',
  render: () => <ButtonWithUseConfirm />,
  component: useConfirm,
};

export const Default = {
  name: 'Default',

  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('button', {name: 'Open confirmation modal'}));

    // The confirmation modal is opened, and shows the title and message
    const confirmationModal = canvas.getByRole('dialog');
    expect(confirmationModal).toBeVisible();
    expect(within(confirmationModal).getByText('The confirmation title')).toBeVisible();
    expect(within(confirmationModal).getByText('A sample confirmation message')).toBeVisible();

    await step('Closing the modal returns false', async () => {
      // Close the modal using the close button
      const closeBtn = await within(canvas.getByRole('dialog')).findByRole('button', {
        name: 'Sluiten',
      });
      await userEvent.click(closeBtn);

      expect(await canvas.findByText('Confirmation result: false')).toBeVisible();
    });

    await step('Confirming the modal returns true', async () => {
      // Open the modal
      await userEvent.click(canvas.getByRole('button', {name: 'Open confirmation modal'}));

      // Close the modal using the confirm button
      const confirmBtn = await within(canvas.getByRole('dialog')).findByRole('button', {
        name: 'Accepteren',
      });
      await userEvent.click(confirmBtn);

      expect(await canvas.findByText('Confirmation result: true')).toBeVisible();
    });

    await step('Cancelling the modal returns false', async () => {
      // Open the modal
      await userEvent.click(canvas.getByRole('button', {name: 'Open confirmation modal'}));

      // Close the modal using the cancel button
      const cancelBtn = await within(canvas.getByRole('dialog')).findByRole('button', {
        name: 'Annuleren',
      });
      await userEvent.click(cancelBtn);

      expect(await canvas.findByText('Confirmation result: false')).toBeVisible();
    });
  },
};
