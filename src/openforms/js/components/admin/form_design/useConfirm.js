import {useState} from 'react';

import ActionButton from '../forms/ActionButton';
import {Modal} from '../modals';

const useConfirm = (title, message) => {
  const [promise, setPromise] = useState(null);

  const confirm = () =>
    new Promise((resolve, reject) => {
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
      contentModifiers={['with-form']}
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
