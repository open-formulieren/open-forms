import React from 'react';
import PropTypes from 'prop-types';
import FormioUtils from 'formiojs/utils';
import {useImmerReducer} from 'use-immer';


const initialState = {
    rules: [],
};


const EMPTY_RULE = {
    logic: {},
    component: '',
    actions: [],
};

const reducer = (draft, action) => {
    switch (action.type) {
        case 'ADD_RULE': {
            draft.rules.push(EMPTY_RULE);
            break;
        }
        default:
            throw new Error(`Unknown action type: ${action.type}`);
    }
};


const FormLogic = ({ formSteps }) => {
    const [state, dispatch] = useImmerReducer(reducer, initialState);

    // key-value map of component.key: component, flattened from all available steps
    const allComponents = formSteps.map(
        step => FormioUtils.flattenComponents(step.configuration.components || [], false)
    ).reduce((acc, currentValue) => ({...acc, ...currentValue}), {});

    console.log(allComponents);

    return (
        <>
            {state.rules.map( (rule, i) => (<Rule key={i} {...rule} allComponents={allComponents} />))}
            <button type="button" onClick={ () => dispatch({type: 'ADD_RULE'}) }>
                Add rule
            </button>
        </>
    );
};

FormLogic.propTypes = {
    formSteps: PropTypes.arrayOf(PropTypes.object).isRequired,
};


const Rule = ({allComponents, logic, component, actions}) => {
    return (
        <div>
            When
            <select>
                {Object.entries(allComponents).map( ([key, comp]) => (
                    <option key={key} value={key}>{comp.label || comp.key}</option>
                ) )}
            </select>
        </div>
    );
};


Rule.propTypes = {
    allComponents: PropTypes.object,
    logic: PropTypes.objects,
    component: PropTypes.string,
    actions: PropTypes.arrayOf(PropTypes.object),
};

export default FormLogic;
