import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import FormioComponentRepresentation from '../FormioComponentRepresentation'

import Types from './types';


const ValueRepresentation = ({ definition=null }) => {
    let valueRepresentation = null;

    switch(definition?.source) {
        case 'component': {
            // initially, we support very simple {"var": "foo"} jsonLogic expressions
            const componentKey = definition?.definition?.var;
            if (!componentKey) {
                return (
                    <FormattedMessage
                        description="JSON editor: unknown FormIO component key"
                        defaultMessage="(missing information)"
                    />
                );
            }
            valueRepresentation = (<FormioComponentRepresentation componentKey={componentKey} />);
            break;
        }
        case 'manual': {
            switch (definition?.type) {
                case 'number':
                case 'boolean':
                case 'string': {
                    const value = definition?.definition;
                    if (value != null) {
                        valueRepresentation = value.toString();
                    }
                    break;
                }
                case 'null': {
                    valueRepresentation = 'null';
                    break;
                }
                case 'array':
                case 'object': {
                    valueRepresentation = (
                        <FormattedMessage
                            description="JSON editor: complex value representation"
                            defaultMessage="(complex value)"
                        />
                    );
                    break;
                }
            }
            break;
        }
    }
    return valueRepresentation;
};

ValueRepresentation.propTypes = {
    definition: Types.VariableDefinition,
};


export default ValueRepresentation;
