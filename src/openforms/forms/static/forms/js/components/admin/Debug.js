import _ from 'lodash';

import React, {useState} from 'react';
import PropTypes from 'prop-types';

import useDebounce from 'react-use/esm/useDebounce';

import FormIOBuilder from '../formio_builder/builder';
import FormStep from './FormStep';

import { useImmerReducer } from 'use-immer';



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



const initialState = {
    configuration: null,
};


const reducer = (draft, action) => {
    switch (action.type) {
        case 'UPDATE_CONFIGURATION': {
            draft.configuration = action.payload;
            break;
        }
        default: {
            throw new Error(`Unknown action ${action.type}`);
        }
    }
};


const noop = console.log;


const Debug = () => {
    const [state, dispatch] = useImmerReducer(reducer, initialState);

    console.log(state.configuration);

    const onChange = (formSchema) => {
        console.log('onChange triggered');
        dispatch({
            type: 'UPDATE_CONFIGURATION',
            payload: formSchema,
        });
    };
    const data = {configuration};
    return (
        <FormStep
            name="Step 1"
            data={data}
            onEdit={onChange}
            onDelete={noop}
            onReorder={noop}
            onReplace={noop}
            errors={{}}
        />
    );
};


export default Debug;
