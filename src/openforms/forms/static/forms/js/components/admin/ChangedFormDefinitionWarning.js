import React, {useState} from 'react';
import PropTypes from 'prop-types';

import Modal from './Modal';


const ChangedFormDefinitionWarning = ({ changed, affectedForms=[] }) => {
    const [modalOpen, setModalOpen] = useState(false);

    const onShowModal = (event) => {
        event.preventDefault();
        setModalOpen(true);
    };

    if (!changed) return null;
    return (
        <>
            <Modal isOpen={modalOpen} closeModal={() => setModalOpen(false)} title={`Formulieren (${affectedForms.length})`}>
                <ul>
                    {affectedForms.map(form => (
                        <li key={form.uuid}>{form.name}</li>
                    ))}
                </ul>
            </Modal>

            <ul className="messagelist">
                <li className="warning">
                    Je bewerkt een bestaande set van formuliervelden! Deze wijziging heeft
                    effect op <a href="#" onClick={onShowModal}>{affectedForms.length} formulier(en)</a>.
                </li>
            </ul>
        </>
    );
};

ChangedFormDefinitionWarning.propTypes = {
    changed: PropTypes.bool,
    affectedForms: PropTypes.arrayOf(PropTypes.shape({
        url: PropTypes.string.isRequired,
        uuid: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        active: PropTypes.bool.isRequired,
    })),
};


export default ChangedFormDefinitionWarning;
