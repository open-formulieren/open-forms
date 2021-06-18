import React from 'react';
import PropTypes from 'prop-types';


const SubmitRow = ({ onSubmit, preventDefault=true, btnText='Opslaan' }) => {

    const onSubmitClick = (event) => {
        if (preventDefault) event.preventDefault();
        onSubmit(event);
    };

    return (
        <div className="submit-row">
            <input
                type="submit"
                value={btnText}
                className="default"
                name="_save"
                onClick={onSubmitClick}
            />
        </div>
    );
};

SubmitRow.propTypes = {
    onSubmit: PropTypes.func.isRequired,
    preventDefault: PropTypes.bool,
    btnText: PropTypes.string,
};


export default SubmitRow;
