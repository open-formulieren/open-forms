import React from 'react';
import PropTypes from 'prop-types';


const SubmitRow = ({ onSubmit, preventDefault=true, btnText='Opslaan', isDefault=false, extraClassName='', children }) => {
    let className = 'submit-row';
    if (extraClassName) {
        className += ` ${extraClassName}`;
    }

    const onSubmitClick = (event) => {
        if (preventDefault) event.preventDefault();
        if (onSubmit) onSubmit(event);
    };

    return (
        <div className={className}>
            { children ?? (
                <input
                    type="submit"
                    value={btnText}
                    className={isDefault ? 'default' : ''}
                    name="_save"
                    onClick={onSubmitClick}
                />
            )}
        </div>
    );
};

SubmitRow.propTypes = {
    onSubmit: PropTypes.func,
    preventDefault: PropTypes.bool,
    isDefault: PropTypes.bool,
    btnText: PropTypes.string,
    extraClassName: PropTypes.string,
    children: PropTypes.node,
};


export default SubmitRow;
