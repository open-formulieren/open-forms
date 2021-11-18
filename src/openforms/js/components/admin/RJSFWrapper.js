import React from 'react';
import PropTypes from 'prop-types';
import Form from '@rjsf/core';

import Field from './forms/Field';
import FAIcon from './FAIcon';


/*
 Adapted from:
 https://github.com/rjsf-team/react-jsonschema-form/blob/master/packages/core/src/components/fields/SchemaField.js#L128
 */
const CustomFieldTemplate = ({
    id,
    label,
    children,
    errors,
    rawErrors,
    rawDescription,
    hidden,
    required,
    displayLabel,
}) => {
    if (hidden) {
        return <div className="hidden">{children}</div>;
    }

    return (
        <div className="rjsf-field">
            <div className={`rjsf-field__field ${rawErrors ? 'rjsf-field__field--error' : ''}`}>
                {(displayLabel && label) && (
                    <label className={`rjsf-field__label ${required ? 'required' : ''}`} htmlFor={id}>
                        {label}
                    </label>
                )}
                <div className="rjsf-field__input">
                    {children}
                </div>
                {rawDescription && (
                    <div className="rjsf-field__help">
                        <FAIcon icon="question-circle" title={rawDescription}/>
                    </div>
                )}
            </div>
            {rawErrors && (
                <div className="rjsf-field__errors">{errors}</div>
            )}
        </div>
    );
};

CustomFieldTemplate.propTypes = {
    id: PropTypes.string,
    label: PropTypes.string,
    children: PropTypes.node.isRequired,
    errors: PropTypes.element,
    rawErrors: PropTypes.arrayOf(PropTypes.string),
    rawDescription: PropTypes.oneOfType([PropTypes.string, PropTypes.element]),
    hidden: PropTypes.bool,
    required: PropTypes.bool,
    displayLabel: PropTypes.bool,
};

/*
Adapted from:
https://github.com/rjsf-team/react-jsonschema-form/blob/master/packages/core/src/components/widgets/CheckboxWidget.js#L5
 */
const CustomCheckboxWidget = ({
    schema,
    id,
    value,
    disabled,
    readonly,
    autofocus,
    onChange,
}) => {
    // The CustomCheckboxWidget is rendered as a children of the CustomFieldTemplate, which makes styling a bit trickier
    return (
        <div className="rjsf-field__checkbox">
            <label className="rjsf-field__label" htmlFor={id}>
                {schema.title}
            </label>
            <input
                type="checkbox"
                id={id}
                checked={typeof value === "undefined" ? false : value}
                disabled={disabled || readonly}
                autoFocus={autofocus}
                onChange={event => onChange(event.target.checked)}
            />
        </div>
    );
};


CustomCheckboxWidget.propTypes = {
    schema: PropTypes.object.isRequired,
    id: PropTypes.string.isRequired,
    value: PropTypes.any,
    required: PropTypes.bool,
    disabled: PropTypes.bool,
    readonly: PropTypes.bool,
    autofocus: PropTypes.bool,
    multiple: PropTypes.bool,
    onChange: PropTypes.func,
};


const FormRjsfWrapper = ({ name, label, schema, formData, onChange, errors }) => {
    let extraErrors = {};

    /*
    add backend validation errors in the correct format. RJSF takes nested objects,
    even for array types, for example:

        const extraErrors = {
            'toEmails': {
                0: {__errors: ['error 1']},
            },
        };

    */
    for (const [key, msg] of errors) {
        const bits = key.split('.');
        // create the nested structure. we can't use lodash, since it creates arrays for
        // indices rather than nested objects.
        let errObj = extraErrors;
        for (const pathBit of bits) {
            if (pathBit === '__proto__' || pathBit === 'prototype') throw new Error('Prototype polution!');
            if (!errObj[pathBit]) errObj[pathBit] = {};
            errObj = errObj[pathBit];
        }
        if (!errObj.__errors) errObj.__errors = [];
        errObj.__errors.push(msg);
    }

    return (
        <Field
            name={name}
            label={label}
            errors={extraErrors ?  [] : errors}
        >
            <Form
                schema={schema}
                formData={formData}
                onChange={onChange}
                FieldTemplate={CustomFieldTemplate}
                widgets={{CheckboxWidget: CustomCheckboxWidget}}
                children={true}
                extraErrors={extraErrors}
                showErrorList={false}
            />
        </Field>
    );
};

FormRjsfWrapper.propTypes = {
    name: PropTypes.string.isRequired,
    label: PropTypes.node.isRequired,
    schema: PropTypes.shape({
        type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
        properties: PropTypes.object,
        required: PropTypes.arrayOf(PropTypes.string),
    }),
    formData: PropTypes.object,
    onChange: PropTypes.func.isRequired,
    errors: PropTypes.array,
};


export default FormRjsfWrapper;
