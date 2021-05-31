import React, {useRef} from 'react';
import {Collapsible} from "../formsets/Collapsible";
import { Form } from 'react-formio';
import Select from "../formsets/Select";
import ErrorList from "../formsets/ErrorList";

const FormIOWrapper = React.forwardRef((props, ref) => (
  <Form {...props} ref={ref} />
));

const FormStep = ({formStepData, formDefinitionChoices, onDelete, onChange, onReorder, errors}) => {
    const formRef = useRef(null);
    const stepName = `Step ${formStepData.order}:`
    const confirmDelete = () => {
        if(window.confirm('Remove step from form?')){
            onDelete(formStepData.order);
        }
    };

    const collapsibleContent = (
        <div className='form-definition'>
            <FormIOWrapper
              ref={formRef}
              form={formStepData.formDefinition.configuration}
              onSubmit={(e) => {console.log(e)}}
              options={{noAlerts: true}}
            />
        </div>
    );

    const collapsibleHeader = (
        <>
            <span className="material-icons" onClick={() => onReorder(formStepData.order, 'up')} title='Move up'>
                keyboard_arrow_up
            </span>
            <span className="material-icons" onClick={() => onReorder(formStepData.order, 'down')} title='Move down'>
                keyboard_arrow_down
            </span>
            <span className="material-icons danger" onClick={confirmDelete} title='delete'>
                delete
            </span>
            <span className="step-name">{stepName}</span>
            <Select
                name="Form definition"
                choices={formDefinitionChoices}
                value={formStepData.formDefinition.uuid}
                onChange={(event) => {onChange(event, formStepData.order)}}
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

const FormSteps = ({formSteps, formDefinitionChoices, onChange, onDelete, onReorder, errors}) => {
    const formStepsBuilders = formSteps.map((formStepData, index) => {
        return (
            <FormStep
                key={index}
                formStepData={formStepData}
                formDefinitionChoices={formDefinitionChoices}
                onDelete={onDelete}
                onChange={onChange}
                onReorder={onReorder}
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


export {FormSteps};
