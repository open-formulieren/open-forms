import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import DeleteIcon from '../DeleteIcon';
import {useOnChanged} from '../form_design/logic/hooks';


const ArrayInput = ({
    name,
    inputType,
    values=[],
    onChange,
    deleteConfirmationMessage,
    addButtonMessage,
    ...extraProps
}) => {
    const intl = useIntl();

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
        <div className="array-input">
            {inputs.map((value, index) => (
                <div key={index} className="array-input__item">
                    <div className="array-input__actions">
                        <DeleteIcon
                            onConfirm={onDelete.bind(null, index)}
                            message={deleteConfirmationMessage || intl.formatMessage({
                                description: "Confirmation message to delete an item from a multi-value input",
                                defaultMessage: "Are you sure you want to delete this item?"
                            })}
                            icon="times"
                        />
                    </div>
                    <input
                        type={inputType}
                        value={value}
                        onChange={onInputChange.bind(null, index)}
                        {...extraProps}
                    />
                </div>
            ))}
            <button type="button" className="button button--plain" onClick={onAdd}>
                { addButtonMessage ||
                    <span className="addlink">
                        <FormattedMessage description="Add item to multi-input field" defaultMessage="Add item" />
                    </span>}
            </button>
        </div>
    )

};

ArrayInput.prototype = {
    name: PropTypes.string.isRequired,
    inputType: PropTypes.string.isRequired,
    values: PropTypes.arrayOf(PropTypes.string),
    onChange: PropTypes.func.isRequired,
    deleteConfirmationMessage: PropTypes.node,
    addButtonMessage: PropTypes.node,
};

export default ArrayInput;
