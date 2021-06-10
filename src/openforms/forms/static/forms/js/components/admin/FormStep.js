import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import usePrevious from 'react-use/esm/usePrevious';

import { Collapsible } from "../formsets/Collapsible";
import Select from "../formsets/Select";
import { getFormDefinitionChoices } from "../utils/form-definition-choices";
import { FormDefinitionsContext } from './Context';
import FormStepDefinition from './FormStepDefinition';
import MaterialIcon from './MaterialIcon';

const FormStepHeader = ({title, currentFormDefinition='', onDelete, onReorder, onReplace}) => {
    const formDefinitions = useContext(FormDefinitionsContext);
    const formDefinitionChoices = getFormDefinitionChoices(formDefinitions);
    return (
        <>
            <MaterialIcon icon="keyboard_arrow_up" title="Move up" onClick={ () => onReorder('up') } />
            <MaterialIcon icon="keyboard_arrow_down" title="Move down" onClick={ () => onReorder('down') } />
            <MaterialIcon icon="delete" extraClassname="danger" title="Delete" onClick={onDelete} />
            <span className="step-name">{title}</span>
            <Select
                name="Form definition"
                choices={formDefinitionChoices}
                value={currentFormDefinition}
                onChange={onReplace}
                className={"step-select"}
            />
        </>
    )
};

FormStepHeader.propTypes = {
    title: PropTypes.string.isRequired,
    currentFormDefinition: PropTypes.string,
    onDelete: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
};

const FormStep = ({ title, data, onEdit, onFieldChange, onDelete, onReorder, onReplace, errors={} }) => {
    const { configuration, formDefinition, name, slug } = data;

    const confirmDelete = () => {
        if(window.confirm('Remove step from form?')){
            onDelete(data);
        }
    };

    const previousFormDefinition = usePrevious(formDefinition);
    let forceBuilderUpdate = false;
    if (previousFormDefinition && previousFormDefinition != formDefinition) {
        forceBuilderUpdate = true;
    }

    const collapsibleHeader = (
        <FormStepHeader
            title={title}
            currentFormDefinition={formDefinition}
            onDelete={confirmDelete}
            onReorder={onReorder}
            onReplace={onReplace}
        />
    );
    const collapsibleContent = (
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
    );

    return (
        <>
            { Object.keys(errors).length ? <div className='fetch-error'>The form step below is invalid.</div> : null }
            <Collapsible
                header={collapsibleHeader}
                content={collapsibleContent}
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
    }).isRequired,
    onEdit: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
    errors: PropTypes.object,
};


export default FormStep;
