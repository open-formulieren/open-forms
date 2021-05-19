import React, {useState, useEffect} from "react";

import useAsync from 'react-use/esm/useAsync';
import {get, post} from './api';


const EditForm = () => {

    const [stepForms, setStepForms] = useState([]);
    const [stepFormValues, setStepFormValues] = useState({});
    const [formStepsToDelete, setFormStepsToDelete] = useState([]);
    // TODO Get this from mount() in index.js
    const formUUID = document.getElementById('form-uuid').innerHTML;

    const {loading: formLoading, value: formValue, error: formError} = useAsync(
        async () => await get(`/api/v1/forms/${formUUID}`)
    );

    const {loading: formDefinitionLoading, value: formDefinitionValues, error: formDefinitionError} = useAsync(
        async () => await get('/api/v1/form-definitions')
    );

    const {loading: formStepsLoading, value: formStepsValues, error: formStepsError} = useAsync(
        async () => await get(`/api/v1/forms/${formUUID}/steps`)
    );

    useEffect(() => {
        if (formStepsValues) {
            const initialStepFormsValues = [];

            formStepsValues.forEach((formStepsValue, index) => {
                initialStepFormsValues.push(
                    <div key={index}>
                        <p>-------------------------</p>
                        <p>Step {index + 1}</p>
                        <button onClick={event => {
                            delete stepFormValues[index + 1];
                            setStepFormValues(stepFormValues);
                            setStepForms(stepForms.filter(element => element.key !== index.toString()));
                            setFormStepsToDelete([...formStepsToDelete, formStepsValue.uuid]);
                        }}>
                            Delete
                        </button>
                        <select name="formDefinitions"
                                value={formStepsValue.formDefinition}
                                onChange={event => {
                                    stepFormValues[index + 1] = event.target.value;
                                    setStepFormValues(stepFormValues);
                                }}>
                            <option key='---' value='---'>---</option>
                            {formDefinitionValues.results.map(definition => {
                                return <option key={definition.slug} value={definition.url}>{definition.name}</option>
                            })}
                        </select>
                        <p>-------------------------</p>
                    </div>
                )
            });

            let initialStepFormValues = {};
            formStepsValues.forEach((formStepsValue, index) => initialStepFormValues[index+1] = formStepsValue.formDefinition);

            setStepFormValues(initialStepFormValues);
            setStepForms(initialStepFormsValues);
        }
    }, [formStepsValues]);


    const getNewStep = () => {
        return (
            <div key={stepForms.length}>
                <p>-------------------------</p>
                <p>Step {stepForms.length+1}</p>
                <button onClick={event => {
                    delete stepFormValues[stepForms.length+1];
                    setStepFormValues(stepFormValues);
                    setStepForms(stepForms.filter(element => element.key !== stepForms.length.toString()));
                }}>
                    Delete
                </button>
                <select name="formDefinitions" onChange={event => {
                    stepFormValues[stepForms.length+1] = event.target.value;
                    setStepFormValues(stepFormValues);
                }}>
                    <option key='---' value='---'>---</option>
                    {formDefinitionValues.results.map(definition => {
                        return <option key={definition.slug} value={definition.url}>{definition.name}</option>
                    })}
                </select>
                <p>-------------------------</p>
            </div>
        )
    };

    return (
        <div className="card">
            <header className="card__header">
                {formValue &&
                    <h2 className="title">Edit Form: {formValue.name}</h2>
                }
            </header>
            <div className="card__body" style={{display: 'flex'}}>

                <div style={{width: '75%'}}>
                    <div>
                        {stepForms}
                    </div>
                    <button
                        onClick={event => {
                            setStepForms([...stepForms, getNewStep()]);
                        }}
                    >
                        Add Step
                    </button>
                    <button
                        onClick={_ => {
                            for (const [key, value] of Object.entries(stepFormValues)) {
                                const data = {
                                    "formDefinition": value
                                };
                                post(`/api/v1/forms/${formUUID}/steps`, data).then(e => {
                                    console.log(e);
                                });
                            }
                        }}
                    >
                        Submit
                    </button>
                    <button
                        onClick={event => {
                            console.log('-------------');
                            console.log('stepFormValues');
                            console.log(stepFormValues);
                            console.log('stepForms');
                            console.log(stepForms);
                            console.log('formStepsToDelete');
                            console.log(formStepsToDelete);
                            console.log('-------------');
                        }}
                    >
                        Print info
                    </button>
                    {/*TODO*/}
                    {/*Need add step button*/}
                    {/*- Add a new step component*/}
                    {/*Need submit button*/}
                    {/*- Submit all the steps*/}
                </div>
            </div>
        </div>
    );
};

export default EditForm;
