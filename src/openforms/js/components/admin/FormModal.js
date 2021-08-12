import React from 'react';
import PropTypes from 'prop-types';

import Modal from './Modal';


const FormModal = ({ isOpen=false, title, closeModal, children }) => (
    <Modal
        isOpen={isOpen}
        title={title}
        closeModal={closeModal}
        contentModifiers={['with-form']}
    >
        <form className="aligned react-modal__form">
            {children}
        </form>
    </Modal>
);


FormModal.propTypes = {
    title: PropTypes.node.isRequired,
    isOpen: PropTypes.bool,
    closeModal: PropTypes.func.isRequired,
    children: PropTypes.node,
};

export default FormModal;
