import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import DeleteIcon from '../DeleteIcon';
import {useOnChanged} from '../form_design/logic/hooks';


const ArrayInput = ({
    name,
    inputType,
    values=[],
    onChange,
    deleteConfirmationMessage='',
    ...extraProps
}) => {
    const [inputs, setInputs] = useState([...values]);

    const onAdd = (event) => {
        setInputs(inputs.concat([""]));
    };

    const onDelete = (index) => {
        let modifiedInputs = [...inputs];
        modifiedInputs.splice(index, 1);
        setInputs(modifiedInputs);
    };

    const onInputChange = (index, event) => {
        let modifiedInputs = [...inputs];
        modifiedInputs[index] = event.target.value;
        setInputs(modifiedInputs);
    };

    useOnChanged(inputs, () => onChange(inputs));

    return (
        <>
            {inputs.map((value, index) => (
                <div key={index}>
                    <div className="logic-rule__actions">
                        <DeleteIcon onConfirm={onDelete.bind(null, index)} message={deleteConfirmationMessage} />
                    </div>
                    <input type={inputType} value={value} onChange={onInputChange.bind(null, index)} {...extraProps}/>
                </div>
            ))}
            <button type="button" className="button button--plain" onClick={onAdd}>
                <span className="addlink">
                    <FormattedMessage description="Add form logic rule button" defaultMessage="Add rule" />
                </span>
            </button>
        </>
    )

};

export default ArrayInput;
