import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Modal from '../Modal';


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
                    <FormattedMessage
                        description="Warning when modifying existing form definitions"
                        defaultMessage="You are modifying an existing form definition! This change affects <link>{count, plural,
                            one {# form}
                            other {# forms}
                        }</link>"
                        values={{
                            count: affectedForms.length,
                            link: (chunks) => (<a href="#" onClick={onShowModal}>{chunks}</a>)
                        }}
                    />
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
