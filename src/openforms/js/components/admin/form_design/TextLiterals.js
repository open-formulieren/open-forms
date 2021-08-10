import React from 'react';
import PropTypes from 'prop-types';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import {TextInput} from '../forms/Inputs';


const TextLiterals = ({ literals, onChange }) => {
    const { beginText, previousText, changeText, confirmText } = literals;
    return (
        <Fieldset>
            <FormRow>
                <Field
                    name="literals.beginText"
                    label="Begin text"
                    helpText="The text that will be displayed at the start of the form to indicate
                                the user can begin to fill in the form.
                                Leave blank to get value from global configuration."
                >
                    <TextInput value={beginText.value} onChange={onChange} maxLength="50" />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="literals.previousText"
                    label="Previous text"
                    helpText="The text that will be displayed in the overview page to go to the previous step.
                                Leave blank to get value from global configuration."
                >
                    <TextInput value={previousText.value} onChange={onChange} maxLength="50" />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="literals.changeText"
                    label="Change text"
                    helpText="The text that will be displayed in the overview page to change a certain step.
                                Leave blank to get value from global configuration."
                >
                    <TextInput value={changeText.value} onChange={onChange} maxLength="50" />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="literals.confirmText"
                    label="Confirm text"
                    helpText="The text that will be displayed in the overview page to confirm
                                the form is filled in correctly.
                                Leave blank to get value from global configuration."
                >
                    <TextInput value={confirmText.value} onChange={onChange} maxLength="50" />
                </Field>
            </FormRow>
        </Fieldset>
    );
};

TextLiterals.propTypes = {
    literals: PropTypes.shape({
        beginText: PropTypes.shape({
            value: PropTypes.string.isRequired,
        }).isRequired,
        previousText: PropTypes.shape({
            value: PropTypes.string.isRequired,
        }).isRequired,
        changeText: PropTypes.shape({
            value: PropTypes.string.isRequired,
        }).isRequired,
        confirmText: PropTypes.shape({
            value: PropTypes.string.isRequired,
        }).isRequired,
    }).isRequired,
    onChange: PropTypes.func.isRequired,
};


export default TextLiterals;
