import React from 'react';
import {FormBuilder} from 'react-formio';
import BEM from "bem.js";
import PropTypes from 'prop-types';
import {BLOCK_FORM_BUILDER, INPUT_ELEMENT, ELEMENT_CONTAINER} from "./constants";

const FormIOBuilder = ({ node }) => {

    const configurationInput = BEM.getChildBEMNode(node, BLOCK_FORM_BUILDER, INPUT_ELEMENT);

    let configuration = {display: 'form'};
    if (configurationInput.value) {
        configuration = JSON.parse(configurationInput.value);
    }

    return (
        <FormBuilder
            form={configuration}
            options={
                {
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
                            }
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
                }
            }
            onChange={formSchema => configurationInput.setAttribute('value', JSON.stringify(formSchema))}
        />
    );
};

FormIOBuilder.propTypes = {
    node: PropTypes.object,
};

export default FormIOBuilder;
