/*
global URLify;
 */
import React from 'react';
import PropTypes from 'prop-types';

import FormIOBuilder from '../formio_builder/builder';
import {Checkbox, TextInput} from "../formsets/Inputs";
import Field from "../formsets/Field";
import FormRow from "../formsets/FormRow";
import useDetectConfigurationChanged from './useDetectConfigurationChanged';
import ChangedFormDefinitionWarning from './ChangedFormDefinitionWarning';
import PluginWarning from "./PluginWarning";

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
 */
const FormStepDefinition = ({ url='', name='', slug='', loginRequired=false, configuration=emptyConfiguration, onChange, onFieldChange, errors, ...props }) => {

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

    const { changed, affectedForms } = useDetectConfigurationChanged(url, configuration);

    return (
        <>
            <ChangedFormDefinitionWarning changed={changed} affectedForms={affectedForms} />
            <PluginWarning loginRequired={loginRequired} configuration={configuration}/>

            <fieldset className="module aligned">
                <h2>Formulierdefinitie</h2>

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
                <FormRow>
                    <Checkbox
                        label="Login required?"
                        name="loginRequired"
                        checked={loginRequired}
                        onChange={(e) => onFieldChange({target: {name: 'loginRequired', value: !loginRequired}})}
                    />
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
    loginRequired: PropTypes.bool,
    onChange: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    errors: PropTypes.object
};


export default FormStepDefinition;
