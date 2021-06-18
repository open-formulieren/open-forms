import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';
import ReactModal from 'react-modal';

import Field from '../formsets/Field';
import FormRow from '../formsets/FormRow';
import Select from '../formsets/Select';
import SubmitRow from "../formsets/SubmitRow";
import { getFormDefinitionChoices } from '../utils/form-definition-choices';
import { FormDefinitionsContext } from './Context';
import FAIcon from './FAIcon';


const NewStepFormDefinitionPicker = ({ onReplace }) => {
    const formDefinitions = useContext(FormDefinitionsContext);
    const formDefinitionChoices = getFormDefinitionChoices(formDefinitions);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedFormDefinition, setSelectedFormDefinition] = useState('');
    const [validationErrors, setValidationErrors] = useState([]);

    const closeModal = () => {
        setIsModalOpen(false);
    };

    const onFormDefinitionConfirmed = () => {
        if (!selectedFormDefinition) {
            setValidationErrors(['Dit veld is verplicht.']);
        } else {
            closeModal();
            onReplace(selectedFormDefinition);
        }
    };

    const onSelectChange = (event) => {
        const { target: {value} } = event;
        setValidationErrors([]);
        setSelectedFormDefinition(value);
    };

    return (
        <div className="tiles tiles--horizontal">
            <button type="button" className="tiles__tile" onClick={() => setIsModalOpen(true)}>
                <FAIcon icon="recycle" extraClassname="fa-2x" title="Selecteer definitie" />
                <span>Gebruik bestaande formulierdefinitie</span>
            </button>

            <span className="tiles__separator">&bull;</span>

            <button type="button" className="tiles__tile">
                <FAIcon icon="pencil-square-o" extraClassname="fa-2x" title="Maak definitie" />
                <span>Maak een nieuwe formulierdefinitie</span>
            </button>

            <ReactModal
                isOpen={isModalOpen}
                onRequestClose={closeModal}
                className="react-modal__content react-modal__content--with-form"
                overlayClassName="react-modal__overlay"
            >
                <header className="react-modal__header">
                    <h2 className="react-modal__title">Gebruik bestaande formulierdefinitie</h2>
                    <FAIcon icon="close" extraClassname="fa-lg react-modal__close" title="Sluiten" onClick={closeModal} />
                </header>

                <form className="aligned react-modal__form">
                    <FormRow>
                        <Field
                            name="form-definition"
                            label="Selecteer formulierdefinitie"
                            errors={validationErrors}
                            required
                        >
                            <Select
                                name="Form definition"
                                choices={formDefinitionChoices}
                                value={selectedFormDefinition}
                                onChange={onSelectChange}
                            />
                        </Field>
                    </FormRow>

                    <SubmitRow onSubmit={onFormDefinitionConfirmed} btnText="Bevestigen" preventDefault />
                </form>
            </ReactModal>

        </div>
    );
};

NewStepFormDefinitionPicker.propTypes = {
    onReplace: PropTypes.func.isRequired,
};

export default NewStepFormDefinitionPicker;
