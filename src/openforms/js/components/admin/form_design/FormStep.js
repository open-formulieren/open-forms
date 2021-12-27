import React from 'react';
import PropTypes from 'prop-types';
import usePrevious from 'react-use/esm/usePrevious';

import FormStepDefinition from './FormStepDefinition';
import NewStepFormDefinitionPicker from './NewStepFormDefinitionPicker';


const FormStep = ({ data, onEdit, onComponentMutated, onFieldChange, onLiteralFieldChange, onReplace}) => {
    const {
        configuration,
        formDefinition,
        name,
        internalName,
        slug,
        literals,
        loginRequired,
        isReusable,
        isNew,
        validationErrors=[],
    } = data;

    const previousFormDefinition = usePrevious(formDefinition);
    let forceBuilderUpdate = false;
    if (previousFormDefinition && previousFormDefinition != formDefinition) {
        forceBuilderUpdate = true;
    }
    // FIXME: find a more robust way than just looking at the step name
    const prevName = usePrevious(name);
    if (!forceBuilderUpdate && prevName && prevName != name) {
        forceBuilderUpdate = true;
    }

    if (isNew) {
        return (
            <NewStepFormDefinitionPicker onReplace={onReplace} />
        );
    }

    return (
        <FormStepDefinition
            name={name}
            internalName={internalName}
            slug={slug}
            url={formDefinition}
            previousText={literals.previousText.value}
            saveText={literals.saveText.value}
            nextText={literals.nextText.value}
            configuration={configuration}
            loginRequired={loginRequired}
            isReusable={isReusable}
            onFieldChange={onFieldChange}
            onLiteralFieldChange={onLiteralFieldChange}
            onChange={onEdit}
            onComponentMutated={onComponentMutated}
            forceUpdate={forceBuilderUpdate}
            errors={validationErrors}
        />
    );
};


FormStep.propTypes = {
    data: PropTypes.shape({
        configuration: PropTypes.object,
        formDefinition: PropTypes.string,
        index: PropTypes.number,
        name: PropTypes.string,
        internalName: PropTypes.string,
        slug: PropTypes.string,
        loginRequired: PropTypes.bool,
        isReusable: PropTypes.bool,
        url: PropTypes.string,
        isNew: PropTypes.bool,
        validationErrors: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
    }).isRequired,
    onEdit: PropTypes.func.isRequired,
    onComponentMutated: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    onLiteralFieldChange: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
};


export default FormStep;
