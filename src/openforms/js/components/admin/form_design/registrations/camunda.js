import groupBy from 'lodash/groupBy';
import React from 'react';
import PropTypes from 'prop-types';
import {useIntl} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import {get} from '../../../../utils/fetch';
import {PROCESS_DEFINITIONS_ENDPOINT} from '../constants';
import Field from '../../forms/Field';
import Select from '../../forms/Select';
import {CustomFieldTemplate} from '../../RJSFWrapper';
import Loader from '../../Loader';


const useLoadProcessDefinitions = () => {
    let processDefinitions;
    const { loading, value, error } = useAsync(
        async () => {
            const response = await get(PROCESS_DEFINITIONS_ENDPOINT);
            if (!response.ok) throw new Error(`Response status: ${response.status}`);
            return response.data;
        }, []
    );

    if (!loading && !error) {
        // transform the process definitions in a grouped structure
        processDefinitions = groupBy(value, 'key');
    }

    return {loading, processDefinitions, error};
};


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
    const intl = useIntl();
    const { processDefinition='', processDefinitionVersion=null } = formData;

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
        </Wrapper>
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


// TODO: handle validation errors properly
const CamundaOptionsForm = ({ name, label, formData, onChange }) => {
    const {loading, processDefinitions, error} = useLoadProcessDefinitions();
    if (error) {
        console.error(error);
        return 'Unexpected error, see console';
    }
    return (
        <Field name={name} label={label} errors={[]}>
            {loading
                ? <Loader />
                : (
                    <FormFields
                        formData={formData}
                        onChange={(formData) => onChange({ formData })}
                        processDefinitions={processDefinitions}
                    />
                )
            }
        </Field>
    );
};

CamundaOptionsForm.propTypes = {
    name: PropTypes.string.isRequired,
    label: PropTypes.node.isRequired,
    formData: PropTypes.shape({ // matches the backend serializer!
        processDefinition: PropTypes.string,
        processDefinitionVersion: PropTypes.number,
    }),
    onChange: PropTypes.func.isRequired,
};


export default CamundaOptionsForm;
