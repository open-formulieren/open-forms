import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import Field from '../formsets/Field';
import FormRow from '../formsets/FormRow';
import Fieldset from '../formsets/Fieldset';
import {TextInput} from '../formsets/Inputs';
import useAsync from 'react-use/esm/useAsync';
import {get, post, put} from '../utils/fetch';
import {FormSteps} from './formsteps-formset';

const FORM_ENDPOINT = '/api/v1/_manage_forms/';

const initialFormState = {
    formName: '',
    formUuid: '',
    formSlug: '',
    formSteps: {
        loading: true,
        data: []
    },
    errors: {}
};

function reducer(draft, action) {
    switch (action.type) {
        /**
         * Form-level actions
         */
        case 'FIELD_CHANGED': {
            const { name, value } = action.payload;
            draft[name] = value;
            break;
        }
        /**
         * FormSteps-level actions
         */
        case 'FORM_STEPS_LOADED': {
            draft.formSteps = {
                loading: false,
                data: action.payload
            };
            break;
        }
        case 'DELETE_STEP': {
            const index = action.payload;
            const unchangedSteps = draft.formSteps.data.slice(0, index);

            const updatedSteps = draft.formSteps.data.slice(index+1).map((step) => {
                step.order = step.order - 1;
                return step;
            });
            draft.formSteps.data = [...unchangedSteps, ...updatedSteps];
            break;
        }
        /**
         * Misc
         */
        case 'SET_FETCH_ERRORS': {
            draft.errors = action.payload;
            break;
        }
        default:
            throw new Error(`Unknown action type: ${action.type}`);
    }
}

const getFormData = async (formUuid, dispatch) => {
    try {
        const formData = await get(`${FORM_ENDPOINT}${formUuid}`);
        dispatch({
            type: 'FORM_STEPS_LOADED',
            payload: formData.formSteps,
        });
    } catch (e) {
        dispatch({type: 'SET_FETCH_ERRORS', payload: e});
    }
};

const FormCreationForm = ({csrftoken, formUuid, formName, formSlug}) => {
    const initialState = {...initialFormState, formUuid, formName, formSlug};
    const [state, dispatch] = useImmerReducer(reducer, initialState);

    useAsync(async () => {
        await getFormData(formUuid, dispatch);
    }, []);

    const onFieldChange = (event) => {
        const { name, value } = event.target;
        dispatch({
            type: 'FIELD_CHANGED',
            payload: {name, value},
        });
    };

    const onChangeFormSteps = (event) => {
      return 'hello';
    };

    const onStepDelete = (index) => {
        dispatch({
            type: 'DELETE_STEP',
            payload: index
        });
    };

    const hasErrors = state.errors.length;
    return (
        <>
            {hasErrors ? <div className='fetch-error'>Dit formulier is ongeldig. Corrigeer de onderstaande fouten.</div> : null}
            <Fieldset>
                <FormRow>
                    <Field
                        name='formUuid'
                        label='Form UUID'
                        helpText='Unique identifier for the form'
                        errors={state.errors.name}
                        required
                    >
                        <TextInput value={state.formUuid} onChange={onFieldChange} />
                    </Field>
                </FormRow>
                <FormRow>
                    <Field
                        name='formName'
                        label='Form name'
                        helpText='Name of the form'
                        errors={state.errors.name}
                        required
                    >
                        <TextInput value={state.formName} onChange={onFieldChange} />
                    </Field>
                </FormRow>
                <FormRow>
                    <Field
                        name='formSlug'
                        label='Form slug'
                        helpText='Slug of the form'
                        errors={state.errors.name}
                        required
                    >
                        <TextInput value={state.formSlug} onChange={onFieldChange} />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset title='Form steps definitions'>
                { state.formSteps.loading ? <div>Loading form steps...</div> :
                    <FormSteps
                        formSteps={state.formSteps.data}
                        onChange={onChangeFormSteps}
                        onDelete={onStepDelete}
                        errors={state.errors}
                    />
                }
            </Fieldset>
        </>
    );
};

FormCreationForm.propTypes = {
    csrftoken: PropTypes.string.isRequired,
    formUuid: PropTypes.string.isRequired,
    formName: PropTypes.string.isRequired,
    formSlug: PropTypes.string.isRequired,
};

export { FormCreationForm };
