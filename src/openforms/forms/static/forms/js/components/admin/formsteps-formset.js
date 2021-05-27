import React, {useRef} from 'react';
import {Collapsible} from "../formsets/Collapsible";
import { Form } from 'react-formio';
import Select from "../formsets/Select";

const FormIOWrapper = React.forwardRef((props, ref) => (
  <Form {...props} ref={ref} />
));

const FormStep = ({formStepData, formDefinitionChoices, onDelete, onChange, errors}) => {
    const formRef = useRef(null);
    const content = (
        <div>
            <FormIOWrapper
              ref={formRef}
              form={formStepData.formDefinition.configuration}
              onSubmit={(e) => {console.log(e)}}
              options={{noAlerts: true}}
            />
        </div>
    );
    const stepName = `Step ${formStepData.order}:`

    return (
        <div>
            <span className="material-icons" onClick={onDelete.bind(null, formStepData.order)} title='delete'>
                delete
            </span>
            <span>{stepName}</span>
            <Select
                name="Form definition"
                choices={formDefinitionChoices}
                value={formStepData.formDefinition.uuid}
                onChange={(event) => {onChange(event, formStepData.order)}}
            />
            <Collapsible
                title='Expand'
                content={content}
            />
        </div>
    );
};

const FormSteps = ({formSteps, formDefinitionChoices, onChange, onDelete, errors}) => {

    const formStepsBuilders = formSteps.map((formStepData, index) => {
        return (
            <FormStep
                key={index}
                formStepData={formStepData}
                formDefinitionChoices={formDefinitionChoices}
                onDelete={onDelete}
                onChange={onChange}
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
