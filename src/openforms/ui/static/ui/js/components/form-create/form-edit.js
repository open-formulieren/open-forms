import React, {useState, useEffect, Fragment} from "react";
import PropTypes from 'prop-types';

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
                    <Fragment key={index}>
                        <td>
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
                            <a
                                onClick={_ => {
                                setStepFormValues(previousState => {
                                    delete previousState[index + 1];
                                    return previousState;
                                });
                                setStepForms(previousState => previousState.filter(element => element.key !== index.toString()));
                                setFormStepsToDelete([...formStepsToDelete, formStepsValue.uuid]);
                            }}>
                                <img src="/static/admin/img/icon-deletelink.svg" alt="Verwijderen"/>
                            </a>
                        </td>
                    </Fragment>
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
            <Fragment key={index}>
                <td>
                    <select name="formDefinitions" onChange={event => {
                        stepFormValues[stepForms.length+1] = event.target.value;
                        setStepFormValues(stepFormValues);
                    }}>
                        <option key='---' value='---'>---</option>
                        {formDefinitionValues.results.map(definition => {
                            return <option key={definition.slug} value={definition.url}>{definition.name}</option>
                        })}
                    </select>
                    <a
                        onClick={event => {
                        setStepFormValues(previousState => {
                            delete previousState[stepForms.length + 1];
                            return previousState;
                        });
                        setStepForms(previousState => previousState.filter(element => element.key !== stepForms.length.toString()));
                    }}>
                        <img src="/static/admin/img/icon-deletelink.svg" alt="Verwijderen"/>
                    </a>
                </td>
            </Fragment>
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
                    <table>
                        <thead>
                            <tr>
                                <th>Order</th>
                                <th>Form Definition</th>
                            </tr>
                        </thead>
                        <tbody>
                            {stepForms.map((stepForm, index) => {
                                return (
                                    <tr key={index}>
                                        <td>{index}</td>
                                        {stepForm}
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                    <div className="submit-row">
                        <button
                            className="button"
                            onClick={_ => {
                                setStepForms([...stepForms, getNewStep()]);
                            }}
                        >
                            Add Step
                        </button>
                        <button
                            className="button"
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
                        <button className="button" onClick={event => getInfo()}>
                            Print info
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

EditForm.propTypes = {
    formUUID: PropTypes.string.isRequired,
};

export default EditForm;
