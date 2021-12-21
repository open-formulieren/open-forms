import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../../forms/Field';
import {CustomFieldTemplate} from '../../RJSFWrapper';


const CamundaOptionsForm = ({ name, label, formData, onChange }) => {
    // TODO: handle validation errors properly

    return (
        <Field name={name} label={label} errors={[]}>
            <div>yep</div>
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
