import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import ActionButton from '../../../forms/ActionButton';
import Select from '../../../forms/Select';
import FormModal from '../../../FormModal';
import {CustomFieldTemplate} from '../../../RJSFWrapper';


// use rjsf wrapper to keep consistent markup/styling
const Wrapper = ({children}) => (
    <form className="rjsf" name="form.registrationBackendOptions">
        <CustomFieldTemplate displayLabel={false} rawErrors={[]}>
            <fieldset id="root">
                {children}
            </fieldset>
        </CustomFieldTemplate>
    </form>
);


const FormFields = ({processDefinitions, formData, onChange}) => {
    const { processDefinition='', processDefinitionVersion=null } = formData;

    const intl = useIntl();
    const [modalOpen, setModalOpen] = useState(true);

    const processDefinitionChoices = Object.entries(processDefinitions).map(([processKey, versions]) => {
        // grab the first version name - it is theoretically possible the process name has changed in
        // another version, but not much we can do about that
        const name = versions[0].name;
        return [processKey, `${name} (${processKey})`];
    });

    const versionChoices = !processDefinition
        ? []
        : processDefinitions[processDefinition].map(version => {
            return [`${version.version}`, `v${version.version}`];
        });


    const onFieldChange = (event) => {
        const {name, value} = event.target;
        const updatedFormData = {...formData, [name]: value};

        switch (name) {
            // if the definition changes, reset the version
            case 'processDefinition': {
                updatedFormData.processDefinitionVersion = null;
                break;
            }
            // normalize blank option to null
            case 'processDefinitionVersion': {
                if (value === '') {
                    updatedFormData.processDefinitionVersion = null;
                } else {
                    updatedFormData.processDefinitionVersion = parseInt(value, 10);
                }
                break;
            }
        }

        // call parent event-handler with fully updated form data object
        onChange(updatedFormData);
    };

    return (
        <>
            <Wrapper>
                <CustomFieldTemplate
                    id="camundaOptions.processDefinition"
                    label={intl.formatMessage({
                        defaultMessage: 'Process',
                        description: 'Camunda \'process definition\' label'
                    })}
                    rawErrors={null} errors={null} // TODO
                    rawDescription={intl.formatMessage({
                        description: 'Camunda \'process definition\' help text',
                        defaultMessage: 'The process definition for which to start a process instance.'
                    })}
                    required
                    displayLabel
                >
                    <Select
                        name="processDefinition"
                        choices={processDefinitionChoices}
                        value={processDefinition}
                        onChange={onFieldChange}
                        allowBlank
                    />
                </CustomFieldTemplate>
                <CustomFieldTemplate
                    id="camundaOptions.processDefinitionVersion"
                    label={intl.formatMessage({
                        defaultMessage: 'Version',
                        description: 'Camunda \'process definition version\' label'
                    })}
                    rawErrors={null} errors={null} // TODO
                    rawDescription={intl.formatMessage({
                        description: 'Camunda \'process definition version\' help text',
                        defaultMessage: 'Which version of the process definition to start. The latest version is used if not specified.'
                    })}
                    required={false}
                    displayLabel
                >
                    <Select
                        name="processDefinitionVersion"
                        choices={versionChoices}
                        value={processDefinitionVersion ? `${processDefinitionVersion}` : ''}
                        onChange={onFieldChange}
                        allowBlank
                    />
                </CustomFieldTemplate>

                <CustomFieldTemplate id="camundaOptions.manageProcessVars" displayLabel={false} rawErrors={null}>
                    <ActionButton
                        text={intl.formatMessage({
                            description: 'Open manage camnda process vars modal button',
                            defaultMessage: 'Manage process variables'
                        })}
                        type="button"
                        onClick={() => setModalOpen(!modalOpen)}
                    />
                </CustomFieldTemplate>

            </Wrapper>

            <FormModal
                isOpen={modalOpen}
                title={<FormattedMessage description="Camunda process var selection modal title" defaultMessage="Manage process variables" />}
                closeModal={() => setModalOpen(false)}
            >
                yolo
            </FormModal>
        </>
    );
};

FormFields.propTypes = {
    processDefinitions: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        key: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        version: PropTypes.number.isRequired,
    }))).isRequired,
    formData: PropTypes.shape({ // matches the backend serializer!
        processDefinition: PropTypes.string,
        processDefinitionVersion: PropTypes.number,
    }),
    onChange: PropTypes.func.isRequired,
};

export default FormFields;
