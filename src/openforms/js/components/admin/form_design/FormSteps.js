import React, {useState} from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import FormStep from './FormStep';
import FormStepsNav from './FormStepsNav';
import Loader from '../Loader';


const FormSteps = ({ steps=[], onEdit, onFieldChange, onLiteralFieldChange, onDelete, onReorder, onReplace, onAdd, submitting=false, errors=[] }) => {
    const [activeStepIndex, setActiveStepIndex] = useState(steps.length ? 0 : null);
    const activeStep = steps.length ? steps[activeStepIndex] : null;

    const className = classNames(
        'edit-panel',
        {'edit-panel--submitting': submitting},
    );

    return (
        <section className={className}>
            { submitting ? (
                <div className="edit-panel__submit-layer">
                    <Loader />
                </div>
            ) : null}


            <div className="edit-panel__nav">
                <FormStepsNav
                    steps={steps}
                    active={activeStep}
                    onActivateStep={setActiveStepIndex}
                    onReorder={onReorder}
                    onDelete={onDelete}
                    onAdd={onAdd}
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
                            onLiteralFieldChange={onLiteralFieldChange.bind(null, activeStepIndex)}
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
        isNew: PropTypes.bool,
    })),
    onEdit: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    onLiteralFieldChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
    onAdd: PropTypes.func.isRequired,
    submitting: PropTypes.bool,
    errors: PropTypes.array,
};


export default FormSteps;
