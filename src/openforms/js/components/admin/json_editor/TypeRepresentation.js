import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage, useIntl} from 'react-intl';

import Types from './types';


export const TYPE_MESSAGES = {
    unset: defineMessage({
        description: 'JSON variable type unset representation',
        defaultMessage: '(unset)',
    }),
    component: defineMessage({
        description: 'JSON variable type "Form field" representation',
        defaultMessage: 'Form field',
    }),
    // manual subset
    string: defineMessage({
        description: 'JSON variable type "string" representation',
        defaultMessage: 'String',
    }),
    number: defineMessage({
        description: 'JSON variable type "number" representation',
        defaultMessage: 'Number',
    }),
    boolean: defineMessage({
        description: 'JSON variable type "boolean" representation',
        defaultMessage: 'Boolean',
    }),
    null: defineMessage({
        description: 'JSON variable type "null" representation',
        defaultMessage: 'Null',
    }),
    object: defineMessage({
        description: 'JSON variable type "object" representation',
        defaultMessage: 'Object',
    }),
    array: defineMessage({
        description: 'JSON variable type "array" representation',
        defaultMessage: 'Array',
    }),
};


const TypeRepresentation = ({ definition=null }) => {
    const intl = useIntl();

    // set default 'unset' in case there's no match
    let typeRepresentationMessage = TYPE_MESSAGES.unset;

    switch(definition?.source) {
        case 'component': {
            typeRepresentationMessage = TYPE_MESSAGES.component;
            break;
        }
        case 'manual': {
            if (!definition.type) break;
            typeRepresentationMessage = TYPE_MESSAGES[definition.type] || TYPE_MESSAGES.unset;
            break;
        }
    }

    return intl.formatMessage(typeRepresentationMessage);
};

TypeRepresentation.propTypes = {
    definition: Types.VariableDefinition,
};


export default TypeRepresentation;
