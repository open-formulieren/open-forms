import React from "react";

import { Form as FormioForm } from 'react-formio';
import { post } from './api';

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


const CreateForm = () => {
  return (
    <div className="card">
      <header className="card__header">
        <h2 className="title">Create Form with React and FormIO</h2>
      </header>
      <div className="card__body" style={{display: 'flex'}}>

        <div style={{width: '75%'}}>
            <FormioForm form={configuration} onSubmit={e => {
                const resp = post('/api/v1/forms' ,e.data);
                console.log(resp);
            }} />
        </div>
      </div>
    </div>
  );
};

export default CreateForm;
