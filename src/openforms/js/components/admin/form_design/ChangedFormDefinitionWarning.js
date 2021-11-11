import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Modal from '../Modal';
import {ChangelistTable, ChangelistColumn} from '../tables';


const AffectedFormType = PropTypes.shape({
    url: PropTypes.string.isRequired,
    uuid: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    active: PropTypes.bool.isRequired,
    adminUrl: PropTypes.string.isRequired,
});


const AffectedFormsTable = ({children: forms}) => (
    <ChangelistTable linkColumn={0} linkProp="adminUrl" rowKey="uuid" data={forms}>

        <ChangelistColumn objProp="name">
            <FormattedMessage description="Form list 'name' column header" defaultMessage="Name" />
        </ChangelistColumn>

        <ChangelistColumn objProp="active" isBool>
            <FormattedMessage description="Form list 'active' column header" defaultMessage="Active" />
        </ChangelistColumn>

    </ChangelistTable>
);

AffectedFormsTable.propTypes = {
    children: PropTypes.arrayOf(AffectedFormType),
};


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
                <AffectedFormsTable>
                    {affectedForms}
                </AffectedFormsTable>
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
    affectedForms: PropTypes.arrayOf(AffectedFormType),
};


export default ChangedFormDefinitionWarning;
