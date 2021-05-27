import React, {useRef} from 'react';
import {Collapsible} from "../formsets/Collapsible";
import { Form } from 'react-formio';

const FormIOWrapper = React.forwardRef((props, ref) => (
  <Form {...props} ref={ref} />
));

const FormDefinitionBuilder = ({formDefinitionData, errors}) => {
    const formRef = useRef(null);
    const content = (
        <div>
            <FormIOWrapper
              ref={formRef}
              form={formDefinitionData.configuration}
              onSubmit={(e) => {console.log(e)}}
              options={{noAlerts: true}}
            />
        </div>
    );

    return (
        <>
            <Collapsible title={formDefinitionData.name} content={content}/>
        </>
    );
};

const FormSteps = ({formSteps, onChange, errors}) => {

    const formStepsBuilders = formSteps.map((formStepData, index) => {
        return (
            <FormDefinitionBuilder key={index} formDefinitionData={formStepData.formDefinition} />
        );
    });

    return (
        <>
            {formStepsBuilders}
        </>
    );
};


export {FormSteps};
