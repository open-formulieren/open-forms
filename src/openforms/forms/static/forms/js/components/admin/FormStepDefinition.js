import React from 'react';
import PropTypes from 'prop-types';

import FormIOBuilder from '../formio_builder/builder';
import {TextInput} from "../formsets/Inputs";
import Field from "../formsets/Field";
import FormRow from "../formsets/FormRow";
import MaterialIcon from "./MaterialIcon";

const emptyConfiguration = {
    display: 'form',
};


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
 * TODO: check what happens when we *replace* the form definition
 *
 */
const FormStepDefinition = ({ url='', name='', slug='', configuration=emptyConfiguration, onChange, onFieldChange, errors, ...props }) => {

    return (
        <div className='form-definition'>
            { url ?
                <div className='warning'>
                    <MaterialIcon icon="warning" title="Warning!" extraClassname='danger'/>
                    You are about to edit an existing form step. This could affect other forms.
                </div> : null
            }
            <div className='form-definition__name'>
                <FormRow>
                    <Field
                        name='name'
                        label='Step name'
                        helpText='Name of the form definition used in this form step'
                        errors={errors.name}
                    >
                        <TextInput value={name} onChange={onFieldChange}/>
                    </Field>
                </FormRow>
                <FormRow>
                    <Field
                        name='slug'
                        label='Step slug'
                        helpText='Slug of the form definition used in this form step'
                        errors={errors.slug}
                    >
                        <TextInput value={slug} onChange={onFieldChange}/>
                    </Field>
                </FormRow>
            </div>
            <div className='form-definition__config'>
                <FormIOBuilder configuration={configuration} onChange={onChange} {...props} />
            </div>
        </div>
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
