import React, {useState} from 'react';
import jsonLogic from 'json-logic-js';
import PropTypes from 'prop-types';

import {TextArea} from '../../forms/Inputs';
import DataPreview from './DataPreview';


const JsonWidget = ({name, logic, onChange}) => {
    const [jsonError, setJsonError] = useState('');
    const [editorValue, setEditorValue] = useState(JSON.stringify(logic));

    const onJsonChange = (event) => {
        const newValue = event.target.value;
        setEditorValue(newValue);
        setJsonError('');

        let updatedJson;

        try {
            updatedJson = JSON.parse(newValue);
        } catch (error) {
            if (error instanceof SyntaxError) {
                setJsonError('Invalid JSON syntax');
                return;
            } else {
                throw error;
            }
        }

        if (!jsonLogic.is_logic(updatedJson)) {
            setJsonError('Invalid JSON logic expression');
            return;
        }

        const fakeEvent = {target: {name: name, value: updatedJson}};
        onChange(fakeEvent);
    };

    return (
        <div className="json-widget">
            <div className="json-widget__input">
                <TextArea
                    name={name}
                    value={editorValue}
                    onChange={onJsonChange}
                    cols={60}
                />
            </div>
            {
                jsonError.length
                ? (<div className="json-widget__error">{jsonError}</div>)
                : null
            }
        </div>
    );
};

JsonWidget.propTypes = {
    name: PropTypes.string.isRequired,
    logic: PropTypes.object.isRequired,
    onChange: PropTypes.func.isRequired,
};


const AdvancedTrigger = ({ name, logic, onChange, error }) => {

    return (
        <div className="logic-trigger">
            <div className={`logic-trigger__json-editor ${ error ? 'logic-trigger__json-editor--error' : ''}`}>
                <JsonWidget name={name} logic={logic} onChange={onChange}/>
                {
                    error
                    ? <div className="logic-trigger__error">{error}</div>
                    : null
                }
            </div>
            <div className="logic-trigger__data-preview">
                <DataPreview data={logic} />
            </div>
        </div>
    );
};

AdvancedTrigger.propTypes = {
    name: PropTypes.string.isRequired,
    logic: PropTypes.object.isRequired,
    onChange: PropTypes.func.isRequired,
    error: PropTypes.string,
};


export default AdvancedTrigger;
