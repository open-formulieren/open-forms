import React from 'react';
import PropTypes from 'prop-types';

import FormStep from './FormStep';
import FormStepsNav from './FormStepsNav';


const FormSteps = ({ steps=[], onEdit, onFieldChange, onDelete, onReorder, onReplace, errors=[] }) => {
    return (
        <section className="edit-panel">
            <div className="edit-panel__nav">
                <FormStepsNav steps={steps} />
            </div>

            <div className="edit-panel__edit-area">
            Dummy
            {/*
                steps.map( (step, index) => (
                    <FormStep
                        key={index}
                        title={`Stap ${index+1}`}
                        data={step}
                        onEdit={onEdit.bind(null, index)}
                        onFieldChange={onFieldChange.bind(null, index)}
                        onDelete={onDelete.bind(null, index)}
                        onReorder={onReorder.bind(null, index)}
                        onReplace={onReplace.bind(null, index)}
                        errors={errors.length ? errors[index] : {}}
                    />
                ) )
            */}
            </div>
        </section>
    );
};

FormSteps.propTypes = {
    steps: PropTypes.arrayOf(PropTypes.shape({
        configuration: PropTypes.object,
        formDefinition: PropTypes.string,
        index: PropTypes.number,
    })),
    onEdit: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
    errors: PropTypes.array,
};


export default FormSteps;
