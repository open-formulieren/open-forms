/*
global URLify;
 */
import React from 'react';
import PropTypes from 'prop-types';

import FormIOBuilder from '../formio_builder/builder';
import {TextInput} from "../formsets/Inputs";
import Field from "../formsets/Field";
import FormRow from "../formsets/FormRow";
import FAIcon from "./FAIcon";

const emptyConfiguration = {
    display: 'form',
};


// if (name === 'name' && !draft.formSteps.data[index].slug) {
//     const slug = URLify(value, 100, false);
//     draft.formSteps.data[index].slug = slug;
// }



/**
 * Load the form builder for a given form definition.
 *
 * Note that the underlying FormIOBuilder creates a ref from the configuration. The
 * actual builder state is maintained by FormioJS itself and we are not driven that
 * state via props - only the initial state!
 *
 * We can solely use the onChange handler to * keep track of our own 'application'
 * state to eventually persist the data. This goes * against React's best practices,
 * but we're fighting the library at this point.
 *
 */
const FormStepDefinition = ({ url='', name='', slug='', configuration=emptyConfiguration, onChange, onFieldChange, errors, ...props }) => {

    const setSlug = () => {
        // do nothing if there's already a slug set
        if (slug) return;

        // sort-of taken from Django's jquery prepopulate module
        const newSlug = URLify(name, 100, false);
        onFieldChange({
            target: {
                name: 'slug',
                value: newSlug,
            }
        });
    };

    return (
        <>
            <fieldset className="module aligned">
                <h2>Formulierdefinitie</h2>

                {/*{ url ?
                    <div className='warning'>
                        <FAIcon icon="exclamation-triangle" title="Warning!" extraClassname='danger'/>
                        You are about to edit an existing form step. This could affect other forms.
                    </div> : null
                }*/}

                <FormRow>
                    <Field
                        name='name'
                        label='Step name'
                        helpText='Name of the form definition used in this form step'
                        errors={errors.name}
                        required
                        fieldBox
                    >
                        <TextInput value={name} onChange={onFieldChange} onBlur={setSlug} />
                    </Field>
                    <Field
                        name='slug'
                        label='Step slug'
                        helpText='Slug of the form definition used in this form step'
                        errors={errors.slug}
                        required
                        fieldBox
                    >
                        <TextInput value={slug} onChange={onFieldChange}/>
                    </Field>
                </FormRow>
            </fieldset>

            <h2>Velden</h2>

            <div className="formio-builder-wrapper">
                <FormIOBuilder configuration={configuration} onChange={onChange} {...props} />
            </div>
        </>
    );
};

FormStepDefinition.propTypes = {
    configuration: PropTypes.object,
    name: PropTypes.string,
    url: PropTypes.string,
    slug: PropTypes.string,
    onChange: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    errors: PropTypes.object
};


export default FormStepDefinition;
