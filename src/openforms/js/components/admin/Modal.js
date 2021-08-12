import React from 'react';
import PropTypes from 'prop-types';
import ReactModal from 'react-modal';
import classNames from 'classnames';

import FAIcon from './FAIcon';

const CONTENT_CLASS_NAME = 'react-modal__content';

const Modal = ({ isOpen=false, title='', closeModal, children, contentModifiers=[] }) => {
    const modifiedClassNames = contentModifiers.map(modifier => `${CONTENT_CLASS_NAME}--${modifier}`);
    const className = classNames(
        CONTENT_CLASS_NAME,
        ...modifiedClassNames
    );
    return (
        <ReactModal isOpen={isOpen} onRequestClose={closeModal} className={className} overlayClassName="react-modal__overlay">
            <header className="react-modal__header">
                { title ? <h2 className="react-modal__title">{title}</h2> : null }
                <FAIcon icon="close" extraClassname="fa-lg react-modal__close" title="Sluiten" onClick={closeModal} />
            </header>
            {children}
        </ReactModal>
    );
};


Modal.propTypes = {
    isOpen: PropTypes.bool,
    title: PropTypes.node,
    closeModal: PropTypes.func.isRequired,
    children: PropTypes.node,
    contentModifiers: PropTypes.arrayOf(PropTypes.string),
};

export default Modal;
