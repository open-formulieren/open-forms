import React from 'react';
import PropTypes from 'prop-types';
import usePrevious from 'react-use/esm/usePrevious';
import {FormattedMessage} from 'react-intl';

import FormStepDefinition from './FormStepDefinition';
import FAIcon from '../FAIcon';
import NewStepFormDefinitionPicker from './NewStepFormDefinitionPicker';


const FormStep = ({ data, onEdit, onFieldChange, onLiteralFieldChange, onReplace, errors={} }) => {
    const { configuration, formDefinition, publicName, internalName, slug, literals, loginRequired, isReusable, isNew } = data;

    const previousFormDefinition = usePrevious(formDefinition);
    let forceBuilderUpdate = false;
    if (previousFormDefinition && previousFormDefinition != formDefinition) {
        forceBuilderUpdate = true;
    }
    // FIXME: find a more robust way than just looking at the step name
    const prevName = usePrevious(publicName);
    if (!forceBuilderUpdate && prevName && prevName != publicName) {
        forceBuilderUpdate = true;
    }

    if (isNew) {
        return (
            <NewStepFormDefinitionPicker onReplace={onReplace} />
        );
    }

    return (
        <>
            { Object.keys(errors).length ? (
                <div className="fetch-error">
                    <FormattedMessage description="Invalid form step error" defaultMessage="The form step below is invalid." />
                </div>
            ) : null }
            <FormStepDefinition
                publicName={publicName}
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
                forceUpdate={forceBuilderUpdate}
                errors={errors}
            />
        </>
    );
};


FormStep.propTypes = {
    data: PropTypes.shape({
        configuration: PropTypes.object,
        formDefinition: PropTypes.string,
        index: PropTypes.number,
        publicName: PropTypes.string,
        internalName: PropTypes.string,
        slug: PropTypes.string,
        loginRequired: PropTypes.bool,
        isReusable: PropTypes.bool,
        url: PropTypes.string,
        isNew: PropTypes.bool,
    }).isRequired,
    onEdit: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    onLiteralFieldChange: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
    errors: PropTypes.object,
};


export default FormStep;
