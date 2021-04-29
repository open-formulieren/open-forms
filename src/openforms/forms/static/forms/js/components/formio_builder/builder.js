import React from 'react';
import ReactDOM from 'react-dom';
import {FormBuilder} from 'react-formio';
import BEM from "bem.js";
import {BLOCK_FORM_BUILDER, INPUT_ELEMENT} from "./constants";

const FormIOBuilder = ({ node }) => {

    const configurationInput = document.getElementById('form-builder__configuration-input');

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

document.addEventListener("DOMContentLoaded", event => {
    const FORM_BUILDERS = BEM.getBEMNodes(BLOCK_FORM_BUILDER);
    [...FORM_BUILDERS].forEach(node => {
        ReactDOM.render(
            <FormIOBuilder node={node} />,
            node
        )
    });
});
