import React, {useRef} from 'react';
import {Collapsible} from "../formsets/Collapsible";
import { Form } from 'react-formio';
import Select from "../formsets/Select";
import PropTypes from "prop-types";

const FormIOWrapper = React.forwardRef((props, ref) => (
  <Form {...props} ref={ref} />
));

const FormStep = ({position, formStepData, formDefinitionChoices, onDelete, onChange, onReorder, errors}) => {
    const formRef = useRef(null);
    const stepName = `Step ${position}:`
    const confirmDelete = () => {
        if(window.confirm('Remove step from form?')){
            onDelete(formStepData);
        }
    };

    const collapsibleContent = (
        <div className='form-definition'>
            <FormIOWrapper
              ref={formRef}
              form={formStepData.configuration}
              onSubmit={(e) => {console.log(e)}}
              options={{noAlerts: true}}
            />
        </div>
    );

    const collapsibleHeader = (
        <>
            <span className="material-icons" onClick={() => onReorder('up')} title='Move up'>
                keyboard_arrow_up
            </span>
            <span className="material-icons" onClick={() => onReorder('down')} title='Move down'>
                keyboard_arrow_down
            </span>
            <span className="material-icons danger" onClick={confirmDelete} title='delete'>
                delete
            </span>
            <span className="step-name">{stepName}</span>
            <Select
                name="Form definition"
                choices={formDefinitionChoices}
                value={formStepData.formDefinition}
                onChange={(event) => {onChange(event)}}
                className={"step-select"}
            />
        </>
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
    formStepData: PropTypes.shape({
        formDefinition: PropTypes.string,
        order: PropTypes.number,
        configuration: PropTypes.object
    }),
    formDefinitionChoices: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
    onDelete: PropTypes.func,
    onChange: PropTypes.func,
    onReorder: PropTypes.func,
    errors: PropTypes.object,
};

const FormSteps = ({formSteps, formDefinitionChoices, onChange, onDelete, onReorder, errors}) => {
    const formStepsBuilders = formSteps.map((formStepData, index) => {
        return (
            <FormStep
                key={index}
                position={index}
                formStepData={formStepData}
                formDefinitionChoices={formDefinitionChoices}
                onDelete={onDelete.bind(null, index)}
                onChange={onChange.bind(null, index)}
                onReorder={onReorder.bind(null, index)}
                errors={errors.formSteps ? errors.formSteps[index] : {}}
            />
        );
    });

    return (
        <>
            {formStepsBuilders}
        </>
    );
};

FormSteps.propTypes = {
    formSteps: PropTypes.arrayOf(PropTypes.shape({
        formDefinition: PropTypes.string,
        index: PropTypes.number,
        configuration: PropTypes.object
    })),
    formDefinitionChoices: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
    onDelete: PropTypes.func,
    onChange: PropTypes.func,
    onReorder: PropTypes.func,
    errors: PropTypes.object,
};

export {FormSteps};
