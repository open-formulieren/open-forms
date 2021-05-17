import React, {useState} from "react";

import {Form as FormioForm} from 'react-formio';
import useAsync from 'react-use/esm/useAsync';
import {get} from './api';
import CreateStepForm from './form-steps';

// Need to send name and slug of form, just those two

const configuration = {
    "display": "form",
    "settings": {
        "pdf": {
            "id": "1ec0f8ee-6685-5d98-a847-26f67b67d6f0",
            "src": "https://files.form.io/pdf/5692b91fd1028f01000407e3/file/1ec0f8ee-6685-5d98-a847-26f67b67d6f0"
        }
    },
    "components": [
        {
            "label": "Add Step",
            "action": "event",
            "showValidations": false,
            "theme": "success",
            "tableView": false,
            "key": "addStep",
            "type": "button",
            "input": true,
            "event": "addStep"
        },
        {
            "type": "button",
            "label": "Submit",
            "key": "submit",
            "disableOnInvalid": true,
            "input": true,
            "tableView": false
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
        }
    ]
};


const EditForm = () => {

    const [stepForms, setStepForms] = useState([]);
    const formUUID = document.getElementById('form-uuid').innerHTML;

    const {loading, value, error} = useAsync(
        async () => await get(`/api/v1/forms/${formUUID}`)
    );

    return (
        <div className="card">
            <header className="card__header">
                {value &&
                    <h2 className="title">Edit Form: {value.name}</h2>
                }
            </header>
            <div className="card__body" style={{display: 'flex'}}>

                <div style={{width: '75%'}}>
                    <div>
                        {stepForms}
                    </div>
                    <FormioForm
                        form={configuration}
                        onCustomEvent={customEvent => {
                          console.log(customEvent);
                          if (customEvent.type === 'addStep') {
                            console.log('Adding step');
                            setStepForms(oldArray => [...oldArray, <CreateStepForm configuration={stepsConfiguration} stepNumber={oldArray.length+1} key={oldArray.length}/>])
                          }
                        }}
                    />
                </div>
            </div>
        </div>
    );
};

export default EditForm;
