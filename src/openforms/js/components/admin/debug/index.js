import React from 'react';
import PropTypes from 'prop-types';
import ReactModal from 'react-modal';
import {IntlProvider} from 'react-intl';

import {ComponentsContext} from '../forms/Context';
import ComplexProcessVariable from '../form_design/registrations/camunda/ComplexProcessVariable';


const allComponents = {
    comp1: {
        type: 'textfield',
        stepLabel: 'Stap 1: Component 1',
    },
    comp2: {
        type: 'textfield',
        stepLabel: 'Stap 1: Component 2',
    },
    comp3: {
        type: 'textfield',
        stepLabel: 'Stap 2: Component 1',
    },
};


const definition = [
    {
        source: 'component',
        definition: {'var': 'comp2'},
    },
];


const Debug = () => {
    return (
        <IntlProvider messages={{}} locale="en" defaultLocale="en">
            <ComponentsContext.Provider value={allComponents}>
                <div style={{position: 'relative'}}>
                    <ComplexProcessVariable
                        name="debug"
                        type="array"
                        definition={definition}
                        onConfirm={console.log}
                    />
                </div>
            </ComponentsContext.Provider>
        </IntlProvider>
    );
};

Debug.propTypes = {
};


ReactModal.setAppElement(document.getElementById('react'));

export default Debug;
