import React from "react";
import {post} from "./api";
import {Form as FormioForm} from "react-formio";

// Just need form definition


const CreateStepForm = ({configuration, submit_url}) => {
    return (
        <div>
            <h2>Form Step</h2>
            <FormioForm form={configuration} onSubmit={e => {
                post(submit_url, e.data).then(response => {
                    console.log(response);
                });
            }}/>
        </div>
    );
};

export default CreateStepForm;
