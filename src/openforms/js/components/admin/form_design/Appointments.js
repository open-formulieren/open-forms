import React from 'react';
import ComponentSelection from "./logic/ComponentSelection";
import {ComponentsContext} from "./logic/Context";
import PropTypes from "prop-types";
import {FormLogic} from "./FormLogic";


const Appointments = ({ availableComponents={} }) => {
    return (
        <ComponentsContext.Provider value={availableComponents}>
            <ComponentSelection
                name="component"
                value=""
                onChange={() => console.log('I changed')}
                // Use below to filter on specific
                // filter={(comp) => (comp.type === componentType)}
            />
        </ComponentsContext.Provider>
    )
};

FormLogic.propTypes = {
    availableComponents: PropTypes.objectOf(
        PropTypes.object, // Formio component objects
    ).isRequired,
};


export default Appointments;
