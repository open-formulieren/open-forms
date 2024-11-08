import PropTypes from 'prop-types';
import React from 'react';

import Modal from './Modal';

const FormModal = ({
  isOpen = false,
  title,
  closeModal,
  onFormSubmit,
  children,
  extraModifiers = [],
  ...props
}) => (
  <Modal
    isOpen={isOpen}
    title={title}
    closeModal={closeModal}
    contentModifiers={['with-form', ...extraModifiers]}
    {...props}
  >
    <form
      className="aligned react-modal__form"
      onSubmit={event => onFormSubmit && onFormSubmit(event)}
      data-testid="modal-form"
    >
      {children}
    </form>
  </Modal>
);

FormModal.propTypes = {
  title: PropTypes.node.isRequired,
  isOpen: PropTypes.bool,
  closeModal: PropTypes.func.isRequired,
  onFormSubmit: PropTypes.func,
  children: PropTypes.node,
  extraModifiers: PropTypes.arrayOf(PropTypes.oneOf(['small', 'large'])),
};

export default FormModal;
