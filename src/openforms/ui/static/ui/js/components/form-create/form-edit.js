import React, {useState, useEffect} from "react";

import useAsync from 'react-use/esm/useAsync';
import {get, post, destroy} from './api';


const EditForm = ({formUUID}) => {

    const [stepForms, setStepForms] = useState([]);
    const [stepFormValues, setStepFormValues] = useState({});
    const [formStepsToDelete, setFormStepsToDelete] = useState([]);

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
                        <p>Step</p>
                        <button onClick={_ => {
                            setStepFormValues(previousState => {
                                delete previousState[index + 1];
                                return previousState;
                            });
                            setStepForms(previousState => previousState.filter(element => element.key !== index.toString()));
                            setFormStepsToDelete([...formStepsToDelete, formStepsValue.uuid]);
                        }}>
                            Delete
                        </button>
                        <select name="formDefinitions"
                                defaultValue={formStepsValue.formDefinition}
                                onChange={event => {
                                    setFormStepsToDelete([...formStepsToDelete, formStepsValue.uuid]);
                                    setStepFormValues(previousState => {
                                        previousState[index + 1] = event.target.value;
                                        return previousState;
                                    });
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

            setStepForms(initialStepFormsValues);
        }
    }, [formStepsValues]);

    const getInfo = () => {
        console.log('-------------');
        console.log('stepFormValues');
        console.log(stepFormValues);
        console.log('stepForms');
        console.log(stepForms);
        console.log('formStepsToDelete');
        console.log(formStepsToDelete);
    };


    const getNewStep = () => {
        return (
            <div key={stepForms.length}>
                <p>-------------------------</p>
                <p>Step</p>
                <button onClick={event => {
                    setStepFormValues(previousState => {
                        delete previousState[stepForms.length + 1];
                        return previousState;
                    });
                    setStepForms(previousState => previousState.filter(element => element.key !== stepForms.length.toString()));
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
                        onClick={_ => {
                            setStepForms([...stepForms, getNewStep()]);
                        }}
                    >
                        Add Step
                    </button>
                    <button
                        onClick={_ => {
                            formStepsToDelete.forEach(formStepUuid => {
                                destroy(`/api/v1/forms/${formUUID}/steps/${formStepUuid}`).then(e => {
                                    console.log(e);
                                });
                            });

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
                    <button onClick={event => getInfo()}>
                        Print info
                    </button>
                </div>
            </div>
        </div>
    );
};

EditForm.propTypes = {
    formUUID: PropTypes.string.isRequired,
};

export default EditForm;
