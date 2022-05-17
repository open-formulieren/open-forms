import _ from 'lodash';

import {get} from '../../../../utils/fetch';
import {FORM_ENDPOINT} from '../constants';
import {COMPONENT_DATATYPES, NO_VARIABLE_COMPONENT} from './constants';


const getComponentDatatype = (component) => {
    if (component.multiple) {
        return [];
    }
    return COMPONENT_DATATYPES[component.type] || '';
};



const updateFormVariables = (mutationType, newComponent, oldComponent, currentFormVariables) => {
    // Not all components are associated with variables
    if (NO_VARIABLE_COMPONENT.includes(newComponent.type)) return currentFormVariables;

    let updatedFormVariables = _.cloneDeep(currentFormVariables);
    const existingKeys = updatedFormVariables.map(variable => variable.key);

    // The 'change' event is emitted for both create and update
    if (mutationType === 'changed') {
        if (!existingKeys.includes(newComponent.key)) {
            // The URL of the form will be added during the onSubmit callback (so that the formUrl is available)
            updatedFormVariables.push({
                name: newComponent.label,
                key: newComponent.key,
                source: 'component',
                dataType: getComponentDatatype(newComponent),
                initial_value: newComponent.defaultValue || '',
            });

            // This is the case where the key of a component has been changed
            if (newComponent.key !== oldComponent.key) {
                updatedFormVariables = updatedFormVariables.filter(variable => variable.key !== oldComponent.key);
            }
        }
    } else if (mutationType === 'removed') {
        // When a component is removed, oldComponent is null
        updatedFormVariables = updatedFormVariables.filter(variable => variable.key !== newComponent.key);
    }

    return updatedFormVariables;
};

const getFormVariables = async (formUuid, dispatch) => {
    let response;
    try {
        response = await get(`${FORM_ENDPOINT}/${formUuid}/variables`);
        if (!response.ok) {
            throw new Error('An error occurred while fetching the form variables.');
        }
    } catch (e) {
        dispatch({type: 'SET_FETCH_ERRORS', payload: {loadingErrors: e.message}});
    }

    return response.data;
};

export {updateFormVariables, getFormVariables};
