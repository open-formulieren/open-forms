import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';
import {useImmerReducer} from 'use-immer';

import ActionButton from '../../../forms/ActionButton';
import Select from '../../../forms/Select';
import FormModal from '../../../FormModal';
import {CustomFieldTemplate} from '../../../RJSFWrapper';
import SelectProcessVariables from './SelectProcessVariables';


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


const initialState = {
    modalOpen: true,
    processVariables: [
        {enabled: true, componentKey: '', alias: ''},
        {enabled: false, componentKey: '', alias: 'explicit'},
        {enabled: true, componentKey: '', alias: ''},
    ],
};

const reducer = (draft, action) => {
    switch(action.type) {
        case 'TOGGLE_PROCESS_VARS_MODAL': {
            draft.modalOpen = !draft.modalOpen;
            break;
        }
        case 'CLOSE_PROCESS_VARS_MODAL': {
            draft.modalOpen = false;
            break;
        }
        case 'MODIFY_PROCESS_VAR': {
            const {index, event: {target: {name, value}}} = action.payload;
            draft.processVariables[index][name] = value;
            break;
        }
        case 'ADD_PROCESS_VAR': {
            draft.processVariables.push({
                enabled: true,
                componentKey: '',
                alias: '',
            });
            break;
        }
        default:
            throw new Error(`Unknown action type: ${action.type}`);
    }
};


const getProcessSelectionChoices = (processDefinitions, processDefinition) => {
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

    return [processDefinitionChoices, versionChoices];
};


const FormFields = ({processDefinitions, formData, onChange}) => {
    const {
        processDefinition='',
        processDefinitionVersion=null,
        // TODO: read procssVariables from formData instead of local state once backend is updated
    } = formData;

    const intl = useIntl();
    const [{modalOpen, processVariables}, dispatch] = useImmerReducer(reducer, initialState);
    const [processDefinitionChoices, versionChoices] = getProcessSelectionChoices(processDefinitions, processDefinition);

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
                        onClick={() => dispatch({type: 'TOGGLE_PROCESS_VARS_MODAL'})}
                    />
                </CustomFieldTemplate>

            </Wrapper>

            <FormModal
                isOpen={modalOpen}
                title={<FormattedMessage description="Camunda process var selection modal title" defaultMessage="Manage process variables" />}
                closeModal={() => dispatch({type: 'CLOSE_PROCESS_VARS_MODAL'})}
            >
                <SelectProcessVariables
                    processVariables={processVariables}
                    onChange={(index, event) => dispatch({type: 'MODIFY_PROCESS_VAR', payload: {index, event}})}
                />
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
