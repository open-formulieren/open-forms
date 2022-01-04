import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';
import produce from 'immer';

import ActionButton, {SubmitAction} from '../../../forms/ActionButton';
import Select from '../../../forms/Select';
import SubmitRow from '../../../forms/SubmitRow';
import FormModal from '../../../FormModal';
import {jsonComplex as COMPLEX_JSON_TYPES} from '../../../json_editor/types';
import {CustomFieldTemplate} from '../../../RJSFWrapper';
import SelectProcessVariables from './SelectProcessVariables';
import ComplexProcessVariables from './ComplexProcessVariables';


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

const EMPTY_PROCESS_VARIABLE = {
    enabled: true,
    componentKey: '',
    alias: '',
};

const EMPTY_COMPLEX_PROCESS_VARIABLE = {
    enabled: true,
    type: 'object',
    definition: {},
    alias: '',
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
        processVariables=[],
        complexProcessVariables=[],
    } = formData;

    const intl = useIntl();
    const [simpleVarsModalOpen, setSimpleVarsModalOpen] = useState(false);
    const [complexVarsModalOpen, setComplexVarsModalOpen] = useState(false);
    const [processDefinitionChoices, versionChoices] = getProcessSelectionChoices(processDefinitions, processDefinition);

    const onFieldChange = (event) => {
        const {name, value} = event.target;
        const updatedFormData = produce(formData, draft => {
            draft[name] = value;

            switch (name) {
                // if the definition changes, reset the version & mapped variables
                case 'processDefinition': {
                    draft.processDefinitionVersion = null;
                    draft.processVariables = []; // reset variables if a different process is used
                    break;
                }
                // normalize blank option to null
                case 'processDefinitionVersion': {
                    if (value === '') {
                        draft.processDefinitionVersion = null;
                    } else {
                        draft.processDefinitionVersion = parseInt(value, 10);
                    }
                    break;
                }
            }
        });

        // call parent event-handler with fully updated form data object
        onChange(updatedFormData);
    };

    const onAddProcessVariable = () => {
        const nextFormData = produce(formData, draft => {
            if (!draft.processVariables) draft.processVariables = [];
            draft.processVariables.push(EMPTY_PROCESS_VARIABLE);
        });
        onChange(nextFormData);
    };

    const onChangeProcessVariable = (index, event) => {
        const {name, value} = event.target;
        const nextFormData = produce(formData, draft => {
            draft.processVariables[index][name] = value;
        });
        onChange(nextFormData);
    };

    const onDeleteProcessVariable = (index) => {
        const nextFormData = produce(formData, draft => {
            draft.processVariables.splice(index, 1);
        });
        onChange(nextFormData);
    };

    const onAddComplexProcessVariable = () => {
        const nextFormData = produce(formData, draft => {
            if (!draft.complexProcessVariables) draft.complexProcessVariables = [];
            draft.complexProcessVariables.push(EMPTY_COMPLEX_PROCESS_VARIABLE);
        });
        onChange(nextFormData);
    };
    const onChangeComplexProcessVariable = (index, event) => {
        const {name, value} = event.target;
        const nextFormData = produce(formData, draft => {
            draft.complexProcessVariables[index][name] = value;
        });
        onChange(nextFormData);
    };
    const onDeleteComplexProcessVariable = (index, event) => {
        const nextFormData = produce(formData, draft => {
            draft.complexProcessVariables.splice(index, 1);
        });
        onChange(nextFormData);
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
                        text={ intl.formatMessage({
                            description: 'Open manage camunda process vars modal button',
                            defaultMessage: 'Manage process variables'
                        })}
                        type="button"
                        onClick={() => setSimpleVarsModalOpen(!simpleVarsModalOpen)}
                    />
                    &nbsp;
                    <FormattedMessage
                        description="Managed Camunda process vars state feedback"
                        defaultMessage="{varCount, plural,
                            =0 {}
                            one {(1 variable mapped)}
                            other {({varCount} variables mapped)}
                        }"
                        values={{varCount: processVariables.length}}
                    />
                </CustomFieldTemplate>

                <CustomFieldTemplate id="camundaOptions.manageComplexProcessVars" displayLabel={false} rawErrors={null}>
                    <ActionButton
                        text={ intl.formatMessage({
                            description: 'Open manage complex camunda process vars modal button',
                            defaultMessage: 'Complex process variables'
                        })}
                        type="button"
                        onClick={() => setComplexVarsModalOpen(!complexVarsModalOpen)}
                    />
                    &nbsp;
                    <FormattedMessage
                        description="Managed complex Camunda process vars state feedback"
                        defaultMessage="{varCount, plural,
                            =0 {}
                            one {(1 variable defined)}
                            other {({varCount} variables defined)}
                        }"
                        values={{varCount: complexProcessVariables.length}}
                    />
                </CustomFieldTemplate>

            </Wrapper>

            <FormModal
                isOpen={simpleVarsModalOpen}
                title={<FormattedMessage description="Camunda process var selection modal title" defaultMessage="Manage process variables" />}
                closeModal={() => setSimpleVarsModalOpen(false)}
            >
                <SelectProcessVariables
                    processVariables={processVariables}
                    onChange={onChangeProcessVariable}
                    onAdd={onAddProcessVariable}
                    onDelete={onDeleteProcessVariable}
                />
                <SubmitRow>
                    <SubmitAction
                        text={intl.formatMessage({description: 'Camunda process variables confirm button', defaultMessage: 'Confirm'})}
                        onClick={(event) => {
                            event.preventDefault();
                            setSimpleVarsModalOpen(false);
                        }}
                    />
                </SubmitRow>
            </FormModal>

            <FormModal
                isOpen={complexVarsModalOpen}
                title={<FormattedMessage description="Camunda complex process vars modal title" defaultMessage="Manage complex process variables" />}
                closeModal={() => setComplexVarsModalOpen(false)}
            >
                <ComplexProcessVariables
                    variables={complexProcessVariables}
                    onChange={onChangeComplexProcessVariable}
                    onAdd={onAddComplexProcessVariable}
                    onDelete={onDeleteComplexProcessVariable}
                />
                <SubmitRow>
                    <SubmitAction
                        text={intl.formatMessage({description: 'Camunda complex process variables confirm button', defaultMessage: 'Confirm'})}
                        onClick={(event) => {
                            event.preventDefault();
                            setComplexVarsModalOpen(false);
                        }}
                    />
                </SubmitRow>
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
        processVariables: PropTypes.arrayOf(PropTypes.shape({
            enabled: PropTypes.bool.isRequired,
            componentKey: PropTypes.string.isRequired,
            alias: PropTypes.string.isRequired,
        })),
        complexProcessVariables: PropTypes.arrayOf(PropTypes.shape({
            enabled: PropTypes.bool,
            alias: PropTypes.string,
            type: PropTypes.oneOf(COMPLEX_JSON_TYPES).isRequired,
            definition: PropTypes.oneOfType([PropTypes.object, PropTypes.array]),
        }))
    }),
    onChange: PropTypes.func.isRequired,
};

export default FormFields;
