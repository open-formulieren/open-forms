import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import FAIcon from '../FAIcon';
import FormModal from '../FormModal';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Select from '../forms/Select';
import SubmitRow from '../forms/SubmitRow';
import { FormDefinitionsContext } from './Context';


const NewStepFormDefinitionPicker = ({ onReplace }) => {
    const intl = useIntl();
    const formDefinitions = useContext(FormDefinitionsContext);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedFormDefinition, setSelectedFormDefinition] = useState('');
    const [validationErrors, setValidationErrors] = useState([]);

    const formDefinitionChoices = formDefinitions.filter(fd => fd.isReusable).map(fd => [fd.url, (fd.internalName || fd.name)]);

    const closeModal = () => {
        setIsModalOpen(false);
    };

    const onFormDefinitionConfirmed = () => {
        if (!selectedFormDefinition) {
            const requiredError = intl.formatMessage({
                description: 'Field required error',
                defaultMessage: 'This field is required.',
            });
            setValidationErrors([requiredError]);
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
                <FAIcon
                    icon="recycle"
                    extraClassname="fa-2x"
                    title={intl.formatMessage({description: 'select definition icon title', defaultMessage: 'Select definition'})}
                />
                <span>
                    <FormattedMessage
                        description="Select form definition tile"
                        defaultMessage="Select existing form definition" />
                </span>
            </button>

            <span className="tiles__separator">&bull;</span>

            <button type="button" className="tiles__tile" onClick={() => {onReplace('')}}>
                <FAIcon
                    icon="pencil-square-o"
                    extraClassname="fa-2x"
                    title={intl.formatMessage({description: 'create form definition icon title', defaultMessage: 'Create definition'})}
                />
                <span>
                    <FormattedMessage
                        description="Create form definition tile"
                        defaultMessage="Create a new form definition" />
                </span>
            </button>

            <FormModal
                isOpen={isModalOpen}
                closeModal={closeModal}
                title={<FormattedMessage
                        description="Form definition selection modal title"
                        defaultMessage="Use existing form definition" />}
            >
                <FormRow>
                    <Field
                        name="form-definition"
                        label={<FormattedMessage description="Form definition select label" defaultMessage="Select form definition" />}
                        errors={validationErrors}
                        required
                    >
                        <Select
                            name="form-definition"
                            choices={formDefinitionChoices}
                            value={selectedFormDefinition}
                            onChange={onSelectChange}
                            allowBlank
                        />
                    </Field>
                </FormRow>

                <SubmitRow
                    onSubmit={onFormDefinitionConfirmed}
                    btnText={intl.formatMessage({description: 'Form definition select confirm button', defaultMessage: 'Confirm'})}
                    isDefault
                    preventDefault
                />
            </FormModal>

        </div>
    );
};

NewStepFormDefinitionPicker.propTypes = {
    onReplace: PropTypes.func.isRequired,
};

export default NewStepFormDefinitionPicker;
