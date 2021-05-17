import React, {useState} from "react";

import useAsync from 'react-use/esm/useAsync';
import {get} from './api';


const EditForm = () => {

    const [stepForms, setStepForms] = useState([]);
    // TODO Get this from mount() in index.js
    const formUUID = document.getElementById('form-uuid').innerHTML;

    const {loading: formLoading, value: formValue, error: formError} = useAsync(
        async () => await get(`/api/v1/forms/${formUUID}`)
    );

    const {loading: formDefinitionLoading, value: formDefinitionValue, error: formDefinitionError} = useAsync(
        async () => await get('/api/v1/form-definitions')
    );

    const getNewStep = () => {
        return (
            <div key={stepForms.length}>
                <p>-------------------------</p>
                <p>Step {stepForms.length+1}</p>
                <select name="formDefinitions">
                    {formDefinitionValue.results.map(definition => {
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
                        onClick={event => setStepForms([...stepForms, getNewStep()])}
                    >
                        Add Step
                    </button>
                    <button
                        onClick={event => console.log(event)}
                    >
                        Submit
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
