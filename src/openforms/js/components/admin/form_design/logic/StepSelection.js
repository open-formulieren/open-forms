import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import Select from '../../forms/Select';
import {FormStepsContext} from '../Context';

const StepSelection = ({name, value, onChange}) => {
    const formSteps = useContext(FormStepsContext);
    const formStepChoices = formSteps.map((step, index) => [step.url, step.name]);

    return (
        <Select
            name={name}
            choices={formStepChoices}
            allowBlank
            onChange={onChange}
            value={value}
        />
    );
};

StepSelection.propTypes = {
    name: PropTypes.string.isRequired,
    value: PropTypes.string,
    onChange: PropTypes.func,
};

export default StepSelection;
