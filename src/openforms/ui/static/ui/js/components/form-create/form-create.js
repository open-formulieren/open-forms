import React, {useState} from "react";

import {Form as FormioForm} from 'react-formio';
import useAsync from 'react-use/esm/useAsync';
import {post} from './api';
import CreateStepForm from './form-steps';

// Need to send name and slug of form, just those two

const configuration = {
    components: [
        {
            type: 'textfield',
            key: 'name',
            label: 'Name',
            placeholder: 'Enter the form name.',
            input: true
        },
        {
            type: 'textfield',
            key: 'slug',
            label: 'Slug',
            placeholder: 'Enter the form slug',
            input: true
        },
        {
            type: 'button',
            action: 'submit',
            label: 'Submit',
            theme: 'primary'
        }
    ]
};

const stepsConfiguration = {
    components: [
        {
            type: "select",
            label: "Choose Form Definition",
            key: "formDefinition",
            placeholder: "Select one",
            data: {
                values: [
                    {
                        value: 'http://localhost:8000/api/v1/form-definitions/13d9c5ff-f538-497c-abfb-6d6b5c161a65',
                        label: 'FormDefinition 000'
                    },
                    {
                        value: 'http://localhost:8000/api/v1/form-definitions/d60aa5dc-bc15-4f73-bdf0-c33785705fea',
                        label: 'FormDefinition 001'
                    },
                ]
            },
            dataSrc: "values",
            template: "<span>{{ item.label }}</span>",
            input: true
        },
        {
            type: 'button',
            action: 'submit',
            label: 'Submit',
            theme: 'primary'
        }
    ]
};


const CreateForm = () => {

    const [formUUID, setFormUUID] = useState();

    const {loading, value, error} = useAsync(
        async () => await get('/api/v1/forms')
    );

    return (
        <div className="card">
            <header className="card__header">
                <h2 className="title">Create Form with React and FormIO</h2>
            </header>
            <div className="card__body" style={{display: 'flex'}}>

                <div style={{width: '75%'}}>
                    <FormioForm form={configuration} onSubmit={e => {
                        post('/api/v1/forms', e.data).then(response => {
                            console.log(e);
                            if (response.status === 201) {
                                setFormUUID(response.data.uuid);
                            }
                        });
                    }}/>
                    {formUUID &&
                    <CreateStepForm configuration={stepsConfiguration} submit_url={`/api/v1/forms/${formUUID}/steps`}/>
                    }
                </div>
            </div>
        </div>
    );
};

export default CreateForm;
