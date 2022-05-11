import React from 'react';
import PropTypes from 'prop-types';

import Modal from './Modal';


const FormModal = ({ isOpen=false, title, closeModal, onFormSubmit, children, extraModifiers=[] }) => (
    <Modal
        isOpen={isOpen}
        title={title}
        closeModal={closeModal}
        contentModifiers={['with-form', ...extraModifiers]}
    >
        <form className="aligned react-modal__form" onSubmit={(event) => onFormSubmit && onFormSubmit(event)}>
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
};

export default FormModal;
