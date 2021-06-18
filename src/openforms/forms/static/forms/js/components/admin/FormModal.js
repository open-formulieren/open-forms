import React from 'react';
import PropTypes from 'prop-types';
import ReactModal from 'react-modal';

import FAIcon from './FAIcon';


const FormModal = ({ isOpen=false, title, closeModal, children }) => (
    <ReactModal
        isOpen={isOpen}
        onRequestClose={closeModal}
        className="react-modal__content react-modal__content--with-form"
        overlayClassName="react-modal__overlay"
    >
        <header className="react-modal__header">
            <h2 className="react-modal__title">{title}</h2>
            <FAIcon icon="close" extraClassname="fa-lg react-modal__close" title="Sluiten" onClick={closeModal} />
        </header>

        <form className="aligned react-modal__form">
            {children}
        </form>
    </ReactModal>
);


FormModal.propTypes = {
    title: PropTypes.string.isRequired,
    isOpen: PropTypes.bool,
    closeModal: PropTypes.func.isRequired,
    children: PropTypes.node,
};

export default FormModal;
