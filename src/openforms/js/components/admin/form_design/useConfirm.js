import {useState} from 'react';

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

  const ConfirmationModal = () => (
    <Modal
      title={title}
      isOpen={promise !== null}
      contentModifiers={['with-form', 'small']}
      closeModal={handleCancel}
    >
      <div style={{flexGrow: 1}}>{message}</div>
      <div className="button-group">
        <ActionButton text="confirm" className="default" onClick={handleConfirm} />
        <ActionButton text="cancel" onClick={handleCancel} />
      </div>
    </Modal>
  );
  return [ConfirmationModal, confirm];
};

export default useConfirm;
