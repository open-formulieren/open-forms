import _ from 'lodash';
import React, {useRef} from 'react';
import {Collapsible} from "../formsets/Collapsible";
import Select from "../formsets/Select";
import PropTypes from "prop-types";
import FormIOBuilder from "../formio_builder/builder";

const emptyComponentsIds = (configuration) => {
    const updatedConfiguration = {...configuration, id: ''};

    if ('components' in configuration) {
        updatedConfiguration.components = updatedConfiguration.components.map((componentConfig, index) => {
            return emptyComponentsIds(componentConfig);
        });
    }
    return updatedConfiguration;
};

const FormStep = ({position, formStepData, initialData, formDefinitionChoices, onDelete, onReplace, onEdit, onReorder, errors}) => {
    const stepName = `Step ${position}:`;

    console.log(initialData);

    const builderRef = useRef(null);

    // if (builderRef.current) {
    //     debugger;
    // }

    const confirmDelete = () => {
        if(window.confirm('Remove step from form?')){
            onDelete(formStepData);
        }
    };

    const collapsibleContent = (
        <div className='form-definition'>
            <FormIOBuilder
                // The builder will fail to render if the components have a pre-filled ID
                // configuration={emptyComponentsIds(formStepData.configuration)}
                configuration={_.cloneDeep(initialData.configuration)}
                onChange={onEdit}
                ref={builderRef}
            />
        </div>
    );

    const collapsibleHeader = (
        <>
            <span className="material-icons" onClick={() => onReorder('up')} title='Move up'>
                keyboard_arrow_up
            </span>
            <span className="material-icons" onClick={() => onReorder('down')} title='Move down'>
                keyboard_arrow_down
            </span>
            <span className="material-icons danger" onClick={confirmDelete} title='delete'>
                delete
            </span>
            <span className="step-name">{stepName}</span>
            <Select
                name="Form definition"
                choices={formDefinitionChoices}
                value={formStepData.formDefinition}
                onChange={(event) => {onReplace(event)}}
                className={"step-select"}
            />
        </>
    );

    console.log(`render ${stepName}`);

    return (
        <>
            { Object.keys(errors).length ? <div className='fetch-error'>The form step below is invalid.</div> : null }
            <span className="step-name">{stepName}</span>
            {collapsibleContent}
            {/*
            <Collapsible
                header={collapsibleHeader}
                content={collapsibleContent}
            />
            */}
        </>
    );
};

FormStep.propTypes = {
    formStepData: PropTypes.shape({
        formDefinition: PropTypes.string,
        order: PropTypes.number,
        configuration: PropTypes.object
    }),
    formDefinitionChoices: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
    onDelete: PropTypes.func,
    onChange: PropTypes.func,
    onReorder: PropTypes.func,
    errors: PropTypes.object,
};

// const FormSteps = ({formSteps, initialFormSteps, formDefinitionChoices, onReplace, onEdit, onDelete, onReorder, errors}) => {
//     const formStepsBuilders = formSteps.map((formStepData, index) => {
//         return (
//             <FormStep
//                 key={index}
//                 position={index}
//                 formStepData={formStepData}
//                 initialData={initialFormSteps[index]}
//                 formDefinitionChoices={formDefinitionChoices}
//                 onDelete={onDelete.bind(null, index)}
//                 onReplace={onReplace.bind(null, index)}
//                 onEdit={onEdit.bind(null, index)}
//                 onReorder={onReorder.bind(null, index)}
//                 errors={errors.formSteps ? errors.formSteps[index] : {}}
//             />
//         );
//     });

//     return (
//         <>
//             {formStepsBuilders}
//         </>
//     );
// };

// FormSteps.propTypes = {
//     formSteps: PropTypes.arrayOf(PropTypes.shape({
//         formDefinition: PropTypes.string,
//         index: PropTypes.number,
//         configuration: PropTypes.object
//     })),
//     formDefinitionChoices: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
//     onDelete: PropTypes.func,
//     onChange: PropTypes.func,
//     onReorder: PropTypes.func,
//     errors: PropTypes.object,
// };


const FormSteps = (props) => {
    // const configuration = props.formSteps[0].configuration;

    const configuration = {
        "display": "form",
        "components": [
            {
                "id": "ecrw1um",
                "key": "voornamen",
                "mask": false,
                "type": "textfield",
                "input": true,
                "label": "Voornamen",
                "hidden": false,
                "plugin": "stufbg",
                "prefix": "",
                "suffix": "",
                "unique": false,
                "widget": {
                    "type": "input"
                },
                "dbIndex": false,
                "overlay": {
                    "top": "",
                    "left": "",
                    "style": "",
                    "width": "",
                    "height": ""
                },
                "prefill": {
                    "plugin": "stufbg",
                    "attribute": "voornamen"
                },
                "tooltip": "",
                "disabled": false,
                "multiple": false,
                "redrawOn": "",
                "tabindex": "",
                "validate": {
                    "custom": "",
                    "unique": false,
                    "pattern": "",
                    "multiple": false,
                    "required": false,
                    "maxLength": "",
                    "minLength": "",
                    "customPrivate": false,
                    "strictDateValidation": false
                },
                "attribute": "bg310:object/bg310:voornamen",
                "autofocus": false,
                "encrypted": false,
                "hideLabel": false,
                "inputMask": "",
                "inputType": "text",
                "modalEdit": false,
                "protected": false,
                "refreshOn": "",
                "tableView": true,
                "attributes": {},
                "errorLabel": "",
                "persistent": true,
                "properties": {},
                "spellcheck": true,
                "validateOn": "change",
                "clearOnHide": true,
                "conditional": {
                    "eq": "",
                    "show": null,
                    "when": null
                },
                "customClass": "",
                "description": "",
                "inputFormat": "plain",
                "placeholder": "",
                "showInEmail": false,
                "defaultValue": null,
                "dataGridLabel": false,
                "labelPosition": "top",
                "showCharCount": false,
                "showWordCount": false,
                "calculateValue": "",
                "calculateServer": false,
                "allowMultipleMasks": false,
                "customDefaultValue": "",
                "allowCalculateOverride": false
            }
        ]
    };

    return (
        <FormIOBuilder
            configuration={configuration}
            onChange={props.onEdit.bind(null, 0)}
        />
    );
};


export {FormSteps};
