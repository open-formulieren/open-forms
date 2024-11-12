import {useState} from 'react';
import {useIntl} from 'react-intl';

import ActionButton from 'components/admin/forms/ActionButton';
import {Modal} from 'components/admin/modals';

const useConfirm = (message, title = '') => {
  const [promise, setPromise] = useState(null);

  const confirm = () =>
    new Promise(resolve => {
      setPromise({resolve});
    });

  const handleClose = () => {
    setPromise(null);
  };

  const handleConfirm = () => {
    promise?.resolve(true);
    handleClose();
  };

  const handleCancel = () => {
    promise?.resolve(false);
    handleClose();
  };

  const ConfirmationModal = () => {
    const intl = useIntl();
    const confirmBtnText = intl.formatMessage({
      description: 'Confirmation modal confirm button',
      defaultMessage: 'Confirm',
    });
    const cancelBtnText = intl.formatMessage({
      description: 'Confirmation modal cancel button',
      defaultMessage: 'Cancel',
    });
    return (
      <Modal
        title={title}
        isOpen={promise !== null}
        contentModifiers={['confirmation']}
        closeModal={handleCancel}
      >
        <p>{message}</p>
        <div className="react-modal__actions">
          <ActionButton text={confirmBtnText} className="default" onClick={handleConfirm} />
          <ActionButton text={cancelBtnText} onClick={handleCancel} />
        </div>
      </Modal>
    );
  };
  return [ConfirmationModal, confirm];
};

export default useConfirm;
