import React from 'react';
import PropTypes from 'prop-types';
import usePrevious from 'react-use/esm/usePrevious';

import FormStepDefinition from './FormStepDefinition';
import FAIcon from './FAIcon';
import NewStepFormDefinitionPicker from './NewStepFormDefinitionPicker';


const FormStep = ({ title, data, onEdit, onFieldChange, onReplace, errors={} }) => {
    const { configuration, formDefinition, name, slug, isNew } = data;

    const previousFormDefinition = usePrevious(formDefinition);
    let forceBuilderUpdate = false;
    if (previousFormDefinition && previousFormDefinition != formDefinition) {
        forceBuilderUpdate = true;
    }

    if (isNew) {
        return (
            <NewStepFormDefinitionPicker onReplace={onReplace} />
        );
    }

    return (
        <>
            { Object.keys(errors).length ? <div className='fetch-error'>The form step below is invalid.</div> : null }
            <FormStepDefinition
                name={name}
                slug={slug}
                url={formDefinition}
                configuration={configuration}
                onFieldChange={onFieldChange}
                onChange={onEdit}
                forceUpdate={forceBuilderUpdate}
                errors={errors}
            />
        </>
    );
};


FormStep.propTypes = {
    title: PropTypes.string.isRequired,
    data: PropTypes.shape({
        configuration: PropTypes.object,
        formDefinition: PropTypes.string,
        index: PropTypes.number,
        name: PropTypes.string,
        slug: PropTypes.string,
        url: PropTypes.string,
        isNew: PropTypes.bool,
    }).isRequired,
    onEdit: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
    errors: PropTypes.object,
};


export default FormStep;
