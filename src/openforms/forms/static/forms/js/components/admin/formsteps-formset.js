import React, {useRef} from 'react';
import {Collapsible} from "../formsets/Collapsible";
import { Form } from 'react-formio';

const FormIOWrapper = React.forwardRef((props, ref) => (
  <Form {...props} ref={ref} />
));

const FormStep = ({formStepData, onDelete, errors}) => {
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
    const stepName = `Step ${formStepData.order}: ${formStepData.formDefinition.name}`

    return (
        <>
            <Collapsible
                title={stepName}
                content={content}
                onDelete={onDelete.bind(null, formStepData.order)}
            />
        </>
    );
};

const FormSteps = ({formSteps, onChange, onDelete, errors}) => {

    const formStepsBuilders = formSteps.map((formStepData, index) => {
        return (
            <FormStep key={index} formStepData={formStepData} onDelete={onDelete}/>
        );
    });

    return (
        <>
            {formStepsBuilders}
        </>
    );
};


export {FormSteps};
