import React from 'react';
import PropTypes from 'prop-types';

import FormStep from './FormStep';


const FormSteps = ({ steps=[], onEdit, onDelete, onReorder, onReplace, errors=[] }) => {
    return (
        <>
            {
                steps.map( (step, index) => (
                    <FormStep
                        key={index}
                        name={`Stap ${index+1}`}
                        data={{configuration: step.configuration}}
                        onEdit={onEdit.bind(null, index)}
                        onDelete={onDelete.bind(null, index)}
                        onReorder={onReorder.bind(null, index)}
                        onReplace={onReplace.bind(null, index)}
                        errors={errors.length ? errors[index] : {}}
                    />
                ) )
            }
        </>
    );
};

FormSteps.propTypes = {
    steps: PropTypes.arrayOf(PropTypes.shape({
        configuration: PropTypes.object,
    })),
    onEdit: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
    errors: PropTypes.array,
};


export default FormSteps;
