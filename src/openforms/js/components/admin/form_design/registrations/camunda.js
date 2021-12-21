import groupBy from 'lodash/groupBy';
import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import {get} from '../../../../utils/fetch';
import Field from '../../forms/Field';
import {CustomFieldTemplate} from '../../RJSFWrapper';
import Loader from '../../Loader';


const PROCESS_DEFINITIONS_ENDPOINT = '/api/v1/registration/plugins/camunda/process-definitions';


const useLoadProcessDefinitions = () => {
    let formDefinitions;
    const { loading, value, error } = useAsync(
        async () => {
            const response = await get(PROCESS_DEFINITIONS_ENDPOINT);
            if (!response.ok) throw new Error(`Response status: ${response.status}`);
            return response.data;
        }, [PROCESS_DEFINITIONS_ENDPOINT]
    );

    if (!loading && !error) {
        // transform the process definitions in a grouped structure
        formDefinitions = groupBy(value, 'key');
    }

    return {loading, formDefinitions, error};
};



const CamundaOptionsForm = ({ name, label, formData, onChange }) => {
    // TODO: handle validation errors properly

    const {loading, formDefinitions, error} = useLoadProcessDefinitions();
    if (error) {
        console.error(error);
        return 'Unexpected error, see console';
    }

    console.log(formDefinitions);

    return (
        <Field name={name} label={label} errors={[]}>
            {loading
                ? <Loader />
                : (
                    <div>yep</div>
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
        processDefinitionVersion: PropTypes.string,
    }),
    onChange: PropTypes.func.isRequired,
};


export default CamundaOptionsForm;
