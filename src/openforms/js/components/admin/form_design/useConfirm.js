import PropTypes from 'prop-types';
import {useState} from 'react';
import {useIntl} from 'react-intl';

import ActionButton from 'components/admin/forms/ActionButton';
import {Modal} from 'components/admin/modals';

const useConfirm = () => {
  const [promise, setPromise] = useState(null);

  const openConfirmationModal = () =>
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

  const confirmationModalProps = {
    isOpen: promise !== null,
    onConfirm: handleConfirm,
    onCancel: handleCancel,
  };

  return {ConfirmationModal, confirmationModalProps, openConfirmationModal};
};

const ConfirmationModal = ({title, message, isOpen, onConfirm, onCancel}) => {
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
    <Modal title={title} isOpen={isOpen} contentModifiers={['confirmation']} closeModal={onCancel}>
      <p>{message}</p>
      <div className="react-modal__actions">
        <ActionButton text={confirmBtnText} className="default" onClick={onConfirm} />
        <ActionButton text={cancelBtnText} onClick={onCancel} />
      </div>
    </Modal>
  );
};

ConfirmationModal.propTypes = {
  title: PropTypes.node,
  message: PropTypes.node.isRequired,
  isOpen: PropTypes.bool.isRequired,
  onConfirm: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

export default useConfirm;
