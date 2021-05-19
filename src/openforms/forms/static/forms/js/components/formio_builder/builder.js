import {FormBuilder} from 'react-formio';
import PropTypes from 'prop-types';
import React from 'react';


const BUILDER_OPTIONS = {
    builder: {
        basic: false,
        advanced: false,
        data: false,
        layout: false,
        premium: false,

        custom: {
            default: true,
            title: 'Formuliervelden',
            weight: 0,
            components: {
                textfield: true,
                textarea: true,
                checkbox: true,
                selectboxes: true,
                select: true,
                radio: true,
                number: true,
                currency: true,
                iban: true,
                email: true,
            }
        },
        custom_layout: {
            title: 'Opmaak',
            weight: 5,
            components: {
                content: true,
                fieldset: true,
            },
        },
        brp: {
            title: 'Basisregistratie Personen',
            weight: 10,
            components: {
                npFamilyMembers: true,
            },
        }

    },
    noDefaultSubmitButton: true,
};


const FormIOBuilder = ({ configuration, onChange }) => {
    return (
        <FormBuilder
            form={configuration}
            options={BUILDER_OPTIONS}
            onChange={formSchema => onChange(formSchema)}
        />
    );
};

FormIOBuilder.propTypes = {
    configuration: PropTypes.object,
    onChange: PropTypes.func,
};

export default FormIOBuilder;
