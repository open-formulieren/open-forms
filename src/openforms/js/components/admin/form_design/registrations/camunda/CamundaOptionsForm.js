import groupBy from 'lodash/groupBy';
import React from 'react';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';

import {get} from '../../../../../utils/fetch';
import {PROCESS_DEFINITIONS_ENDPOINT} from '../../constants';
import Field from '../../../forms/Field';
import Loader from '../../../Loader';
import FormFields from './FormFields';


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
        processVariables: PropTypes.arrayOf(PropTypes.shape({
            enabled: PropTypes.bool.isRequired,
            componentKey: PropTypes.string.isRequired,
            alias: PropTypes.string.isRequired,
        })),
    }),
    onChange: PropTypes.func.isRequired,
};


export default CamundaOptionsForm;
