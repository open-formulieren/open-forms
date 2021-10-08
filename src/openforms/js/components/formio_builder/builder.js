import cloneDeep from 'lodash/cloneDeep';
import React, {useRef, useEffect, useState} from 'react';
import PropTypes from 'prop-types';
import {FormBuilder} from 'react-formio';

import nlStrings from './translation';


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
                date: true,
                signature: true,
                time: true,
                phoneNumber: true,
                bsn: true,
                postcode: true,
                file: true,
            }
        },
        custom_layout: {
            title: 'Opmaak',
            weight: 5,
            components: {
                content: true,
                fieldset: true,
                columns: true,
            },
        }
    },
    noDefaultSubmitButton: true,
    language: 'nl',
    i18n: {
        nl: nlStrings
    }
};


const FormIOBuilder = ({ configuration, onChange, forceUpdate=false }) => {
    // the deep clone is needed to create a mutable object, as the FormBuilder
    // mutates this object when forms are edited.
    const clone = cloneDeep(configuration);
    // using a ref that is never updated allows us to create a mutable object _once_
    // and hold that reference and pass it down to the builder. Because the reference
    // never changes, the prop never changes, and re-renders of the form builder are
    // avoided. This prevents an infinite loop, reported here: https://github.com/formio/react/issues/386
    // The onChange events fires for every render. So, if the onChange event causes props
    // to change (by reference, not by value!), you end up in an infite loop.
    //
    // This approach effectively pins the FormBuilder.form prop reference.
    const formRef = useRef(clone);

    // track some state to force re-renders, and we can also keep track of the amount of
    // re-renders that way for debugging purposes.
    const [rerenders, setRerenders] = useState(0);

    // if an update must be forced, we mutate the ref state to point to the new
    // configuration, which causes the form builder to re-render the new configuration.
    useEffect(
        () => {
            if (forceUpdate) {
                formRef.current = clone;
                setRerenders(rerenders + 1);
            }
        }
    );

    return (
        <FormBuilder
            form={formRef.current}
            options={BUILDER_OPTIONS}
            onChange={formSchema => onChange(cloneDeep(formSchema))}
        />
    );
};

FormIOBuilder.propTypes = {
    configuration: PropTypes.object,
    onChange: PropTypes.func,
    forceUpdate: PropTypes.bool,
};

export default FormIOBuilder;
