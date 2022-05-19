import cloneDeep from 'lodash/cloneDeep';
import React, {useRef, useEffect, useState} from 'react';
import PropTypes from 'prop-types';
import {FormBuilder, Templates} from 'react-formio';

import jsonScriptToVar from '../../utils/json-script';
import nlStrings from './translation';
import customTemplates from './customTemplates';

Templates.current = customTemplates;


const getBuilderOptions = () => {

    const maxFileUploadSize = jsonScriptToVar('setting-MAX_FILE_UPLOAD_SIZE');
    const formFieldsRequiredDefault = jsonScriptToVar('config-REQUIRED_DEFAULT');

    return {
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
                    email: true,
                    date: true,
                    time: true,
                    phoneNumber: true,
                    postcode: true,
                    file: true,
                    password: true,
                }
            },
            custom_special: {
                title: 'Special fields',
                weight: 5,
                components: {
                    iban: true,
                    licenseplate: true,
                    bsn: true,
                    npFamilyMembers: true,
                    signature: true,
                    coSign: true,
                    map: true,
                },
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
        },
        evalContext: {
            serverUploadLimit: maxFileUploadSize,
            requiredDefault: formFieldsRequiredDefault,
        },
        editors: {
            ckeditor: {
                settings: {
                    toolbar: {
                        items: ["heading", "fontFamily", "fontSize", "fontColor", "|", "bold", "italic", "link", "bulletedList", "numberedList", "|", "indent", "outdent", "|", "imageUpload", "blockQuote", "insertTable", "mediaEmbed", "alignment:left", "alignment:right", "alignment:center", "undo", "redo"]
                    },
                    link: {
                        decorators: {
                            openInNewTab: {
                                mode: 'manual',
                                label: 'Open in a new tab',
                                defaultValue: true,			// This option will be selected by default.
                                attributes: {
                                    target: '_blank',
                                    rel: 'noopener noreferrer'
                                }
                            }
                        }
                    },
                    fontColor: {
                        colors: jsonScriptToVar('config-RICH_TEXT_COLORS'),
                    }
                }
            }
        }
    };
};


const FormIOBuilder = ({ configuration, onChange, onComponentMutated, forceUpdate=false }) => {
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

    // props need to be immutable to not end up in infinite loops
    const [builderOptions] = useState(getBuilderOptions());

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

    const extraProps = {};

    if (onComponentMutated) {
        extraProps.onSaveComponent = onComponentMutated.bind(null, 'changed');
        extraProps.onDeleteComponent = onComponentMutated.bind(null, 'removed');
    }

    return (
        <FormBuilder
            form={formRef.current}
            options={builderOptions}
            onChange={formSchema => onChange(cloneDeep(formSchema))}
            {...extraProps}
        />
    );
};

FormIOBuilder.propTypes = {
    configuration: PropTypes.object,
    onChange: PropTypes.func,
    onComponentMutated: PropTypes.func,
    forceUpdate: PropTypes.bool,
};

export default FormIOBuilder;
