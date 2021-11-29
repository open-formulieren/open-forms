import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Fieldset from '../forms/Fieldset';


export const EMPTY_PRICE_RULE = {
    uuid: '',
    form: '',
    jsonLogicTrigger: {},
    price: '',
};


export const PriceLogic = ({ rules=[], availableComponents={}, onChange, onDelete, onAdd }) => {
    return (
        <Fieldset
            extraClassName="admin-fieldset"
            title={<FormattedMessage description="Dynamic pricing fieldset title" defaultMessage="Pricing logic" />}
        >
        </Fieldset>
    );
};

PriceLogic.propTypes = {
    rules: PropTypes.arrayOf(PropTypes.object),
    availableComponents: PropTypes.objectOf(
        PropTypes.object, // Formio component objects
    ).isRequired,
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onAdd: PropTypes.func.isRequired,
};


export default PriceLogic;
