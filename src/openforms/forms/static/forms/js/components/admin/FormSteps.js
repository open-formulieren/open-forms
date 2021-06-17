import React, {useState} from 'react';
import PropTypes from 'prop-types';

import FormStep from './FormStep';
import FormStepsNav from './FormStepsNav';


const FormSteps = ({ steps=[], onEdit, onFieldChange, onDelete, onReorder, onReplace, errors=[] }) => {
    const [activeStepIndex, setActiveStepIndex] = useState(steps.length ? 0 : null);
    const activeStep = steps.length ? steps[activeStepIndex] : null;

    return (
        <section className="edit-panel">
            <div className="edit-panel__nav">
                <FormStepsNav
                    steps={steps}
                    active={activeStep}
                    onActivateStep={(step) => setActiveStepIndex(steps.indexOf(step))}
                    onReorder={onReorder}
                />
            </div>

            <div className="edit-panel__edit-area">
                { activeStep
                    ? (
                        <FormStep
                            title={`Stap ${activeStepIndex+1}`}
                            data={activeStep}
                            onEdit={onEdit.bind(null, activeStepIndex)}
                            onFieldChange={onFieldChange.bind(null, activeStepIndex)}
                            onDelete={onDelete.bind(null, activeStepIndex)}
                            onReplace={onReplace.bind(null, activeStepIndex)}
                            errors={errors.length ? errors[activeStepIndex] : {}}
                        />
                    )
                    : 'Select a step to view or modify.' }

            </div>
        </section>
    );
};

FormSteps.propTypes = {
    steps: PropTypes.arrayOf(PropTypes.shape({
        configuration: PropTypes.object,
        formDefinition: PropTypes.string,
        index: PropTypes.number,
        name: PropTypes.string,
        slug: PropTypes.string,
        url: PropTypes.string,
    })),
    onEdit: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
    errors: PropTypes.array,
};


export default FormSteps;
