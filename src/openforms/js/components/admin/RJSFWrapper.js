import React from 'react';
import PropTypes from 'prop-types';
import Form from '@rjsf/core';

import Field from './forms/Field';
import FAIcon from './FAIcon';


const DefaultTemplate = ({
    id,
    label,
    children,
    errors,
    help,
    description,
    hidden,
    required,
    displayLabel,
}) => {
    if (hidden) {
        return <div className="hidden">{children}</div>;
    }

    const descriptionText = description?.props?.description;

    return (
        <div className="rjsf-field">
            {(displayLabel && label) && (
                <label className={`rjsf-field__label ${required ? 'required' : ''}`} htmlFor={id}>
                    {label}
                </label>
            )}
            <div className="rjsf-field__input">
                {children}
            </div>
            {descriptionText && (
                <div className="rjsf-field__help">
                    <FAIcon icon="question-circle" title={descriptionText}/>
                </div>
            )}
            {errors}
        </div>
    );
};


const CustomObjectFieldTemplate = ({
    idSchema,
    properties,
    uiSchema,
    ...extraProps
})  => {
    const updatedProperties = properties.map((property) => {
        let content = property.content;
        content.props.uiSchema["ui:FieldTemplate"] = DefaultTemplate;
        return content;
    });
    return (
        <fieldset id={idSchema.$id}>
          {updatedProperties}
        </fieldset>
    );
}


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
                ObjectFieldTemplate={CustomObjectFieldTemplate}
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
