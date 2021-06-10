import React from 'react';
import PropTypes from 'prop-types';

import FormStepDefinition from './FormStepDefinition';
import MaterialIcon from './MaterialIcon';


const FormStepHeader = ({name, onDelete, onReorder, onReplace}) => {
    const confirmDelete = () => {
        if(window.confirm('Remove step from form?')){
            onDelete(formStepData);
        }
    };
    return (
        <>
            <MaterialIcon icon="keyboard_arrow_up" title="Move up" onClick={ () => onReorder('up') } />
            <MaterialIcon icon="keyboard_arrow_down" title="Move down" onClick={ () => onReorder('down') } />
            <MaterialIcon icon="delete" extraClassname="danger" title="Delete" onClick={confirmDelete} />
            <span className="step-name">{name}</span>
            {/* TODO: add form definition select back */}
            {/*<Select
                name="Form definition"
                choices={formDefinitionChoices}
                value={formStepData.formDefinition}
                onChange={onReplace}
                className={"step-select"}
            />*/}
        </>
    )
};

FormStepHeader.propTypes = {
    name: PropTypes.string.isRequired,
    onDelete: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
};



const FormStep = ({ name, data, onEdit, onDelete, onReorder, onReplace, errors={} }) => {
    const { configuration } = data;
    return (
        <>
            { Object.keys(errors).length ? <div className='fetch-error'>The form step below is invalid.</div> : null }
            {/*
            <Collapsible
                header={collapsibleHeader}
                content={collapsibleContent}
            />
            */}
            <FormStepHeader name={name} onDelete={onDelete} onReorder={onReorder} onReplace={onReplace} />
            <FormStepDefinition initialConfiguration={configuration} onChange={onEdit} />
        </>
    );
};

FormStep.propTypes = {
    name: PropTypes.string.isRequired,
    data: PropTypes.object.isRequired,
    onEdit: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
    errors: PropTypes.object,
};


export default FormStep;
